"""
Generate DIP switches
"""

import sys
from os import path
from uuid import uuid4

from typing import List, Optional, Tuple, Union

from common import init_cache, now, save_cache
from entities.attribute import Attribute, AttributeType
from entities.common import (
    Align,
    Angle,
    Author,
    Category,
    Circle,
    Created,
    Deprecated,
    Description,
    Diameter,
    Fill,
    GeneratedBy,
    GrabArea,
    Height,
    Keywords,
    Layer,
    Length,
    Name,
    Polygon,
    Position,
    Position3D,
    Resource,
    Rotation,
    Rotation3D,
    Text,
    Value,
    Version,
    Vertex,
    Width,
)
from entities.component import (
    Clock,
    Component,
    DefaultValue,
    ForcedNet,
    Gate,
    Negated,
    Norm,
    PinSignalMap,
    Prefix,
    Required,
    Role,
    SchematicOnly,
    Signal,
    SignalUUID,
    Suffix,
    SymbolUUID,
    TextDesignator,
    Variant,
)
from entities.device import ComponentPad, ComponentUUID, Device, Manufacturer, PackageUUID, Part
from entities.package import (
    AssemblyType,
    AutoRotate,
    ComponentSide,
    CopperClearance,
    DrillDiameter,
    Footprint,
    Footprint3DModel,
    FootprintPad,
    LetterSpacing,
    LineSpacing,
    Mirror,
    Package,
    Package3DModel,
    PackagePad,
    PackagePadUuid,
    PadFunction,
    PadHole,
    Shape,
    ShapeRadius,
    Size,
    SolderPasteConfig,
    StopMaskConfig,
    StrokeText,
    StrokeWidth,
)
from entities.symbol import NameAlign, NameHeight, NamePosition, NameRotation, Symbol
from entities.symbol import Pin as SymbolPin

generator = 'librepcb-parts-generator (generate_dip_switches.py)'

# Initialize UUID cache
uuid_cache_file = 'uuid_cache_dip_switches.csv'
uuid_cache = init_cache(uuid_cache_file)


def uuid(category: str, full_name: str, identifier: str) -> str:
    key = '{}-{}-{}'.format(category, full_name, identifier).lower().replace(' ', '~')
    if key not in uuid_cache:
        uuid_cache[key] = str(uuid4())
    return uuid_cache[key]


def get_y(pin_index: int, circuits: int, pitch: float) -> float:
    y0 = (circuits - 1) * pitch / 2
    dy = y0 - family.lead_config.pitch_y * (pin_index % circuits)
    if pin_index < circuits:
        return dy
    else:
        return -dy


class VariantConfig:
    def __init__(self, id: str, name: str, description: str, norm: Norm, norm_name: str):
        self.id = id
        self.name = name
        self.description = description
        self.norm = norm
        self.norm_name = norm_name


VARIANT_EU = VariantConfig(
    id='eu', name='EU', description='European', norm=Norm.IEC_60617, norm_name='IEC 60617'
)
VARIANT_US = VariantConfig(
    id='us', name='US', description='American', norm=Norm.IEEE_315, norm_name='IEEE 315'
)


class ThtLeadConfig:
    def __init__(
        self,
        pitch_x: float,
        pitch_y: float,
        drill: float,
        pad_diameter: float,
        thickness: float,
        width_top: float,
        width_bottom: float,
        length: float,
    ):
        self.pitch_x = pitch_x
        self.pitch_y = pitch_y
        self.drill = drill
        self.pad_diameter = pad_diameter
        self.thickness = thickness
        self.width_top = width_top
        self.width_bottom = width_bottom
        self.length = length  # From PCB surface to end of lead (Z)


class GullWingLeadConfig:
    def __init__(
        self,
        pitch_x: float,
        pitch_y: float,
        pad_size_x: float,
        pad_size_y: float,
        thickness: float,
        width: float,
        span: float,
    ):
        self.pitch_x = pitch_x
        self.pitch_y = pitch_y
        self.pad_size_x = pad_size_x
        self.pad_size_y = pad_size_y
        self.thickness = thickness
        self.width = width
        self.span = span


class Family:
    def __init__(
        self,
        manufacturer: str,
        pkg_name_prefix: str,
        dev_name_prefix: str,
        body_size_x: float,
        body_size_z: float,
        body_standoff: float,
        window_size: Tuple[float, float],
        actuator_size: float,
        actuator_height: float,
        actuator_color: str,
        lead_config: Union[ThtLeadConfig, GullWingLeadConfig],
        datasheet: Optional[str],
        datasheet_name: Optional[str],
        keywords: List[str],
    ) -> None:
        self.manufacturer = manufacturer
        self.pkg_name_prefix = pkg_name_prefix
        self.dev_name_prefix = dev_name_prefix
        self.body_size_x = body_size_x
        self.body_size_z = body_size_z
        self.body_standoff = body_standoff
        self.window_size = window_size
        self.actuator_size = actuator_size
        self.actuator_height = actuator_height
        self.actuator_color = actuator_color
        self.lead_config = lead_config
        self.datasheet = datasheet
        self.datasheet_name = datasheet_name
        self.keywords = keywords


class Model:
    def __init__(
        self,
        name: str,
        circuits: int,
        body_size_y: float,
        parts: List[Part],
        common_part_attributes: Optional[List[Attribute]] = None,
    ) -> None:
        self.name = name
        self.circuits = circuits
        self.body_size_y = body_size_y
        self.parts = parts
        self.common_part_attributes = common_part_attributes or []

    def uuid_key(self, family: Family) -> str:
        return (
            '{}-{}'.format(family.pkg_name_prefix, model.name)
            .lower()
            .replace(' ', '')
            .replace(',', 'p')
        )

    def get_description(self, family: Family) -> str:
        s = f'{self.circuits}x DIP switch from {family.manufacturer}.'
        s += f'\n\nBody Size: {family.body_size_x:.2f} x {model.body_size_y:.2f} mm'
        if isinstance(family.lead_config, ThtLeadConfig):
            s += f'\nPitch: {family.lead_config.pitch_x:.2f} x {family.lead_config.pitch_y:.2f} mm'
        if isinstance(family.lead_config, GullWingLeadConfig):
            s += f'\nLead Span: {family.lead_config.span:.2f} mm'
        if not isinstance(family.lead_config, ThtLeadConfig):
            s += f'\nLead Y-Pitch: {family.lead_config.pitch_y:.2f} mm'
        s += f'\nActuator Height: {family.actuator_height:.2f} mm'
        s += f'\n\nGenerated with {generator}'
        return s

    def get_keywords(self, family: Family) -> str:
        return ','.join(
            [
                'dip',
                'slide',
                'switch',
            ]
            + family.keywords
        )


def generate_sym(
    library: str,
    author: str,
    name: str,
    cmpcat: str,
    keywords: str,
    circuits: int,
    version: str,
    variant: VariantConfig,
    create_date: Optional[str] = None,
) -> None:
    full_name = name.format(circuits=circuits, variant=variant)

    def _uuid(identifier: str) -> str:
        return uuid('sym', f'{variant.id}-{circuits:02}', identifier)

    uuid_sym = _uuid('sym')

    print('Generating {}: {}'.format(full_name, uuid_sym))

    # Symbol
    symbol = Symbol(
        uuid=uuid_sym,
        name=Name(full_name),
        description=Description(
            f'DIP switch array with {circuits} circuits, {variant.description} symbol '
            f'({variant.norm_name}).\n\nGenerated with {generator}'
        ),
        keywords=Keywords(keywords),
        author=Author(author),
        version=Version(version),
        created=Created(create_date or now()),
        deprecated=Deprecated(False),
        generated_by=GeneratedBy(''),
        categories=[Category(cmpcat)],
    )

    # Pins
    dx = 5.08
    pin1_y = ((circuits - 1) // 2) * 2.54
    pin_length = 2.0
    pin_name_y = 0.2 if (variant == VARIANT_US) else 0.0
    for circuit in range(1, circuits + 1):
        for i in range(2):
            x = [-dx, dx][i]
            y = pin1_y - (circuit - 1) * 2.54
            symbol.add_pin(
                SymbolPin(
                    _uuid('pin-{:02}{}'.format(circuit, ['a', 'b'][i])),
                    Name([f'{circuit}', f'{circuit}.2'][i]),
                    Position(x, y),
                    Rotation([0, 180][i]),
                    Length(pin_length),
                    NamePosition(pin_length + 0.5, [pin_name_y, -0.5][i]),
                    NameRotation(0.0),
                    NameHeight(2.0),
                    NameAlign(['left bottom', 'left top'][i]),
                )
            )

    # Outline
    dx -= pin_length
    y_top = pin1_y + 2.54
    y_bot = pin1_y - circuits * 2.54
    symbol.add_polygon(
        Polygon(
            _uuid('polygon-outline'),
            Layer('sym_outlines'),
            Width(0.2),
            Fill(False),
            GrabArea(True),
            [
                Vertex(Position(-dx, y_top), Angle(0.0)),
                Vertex(Position(dx, y_top), Angle(0.0)),
                Vertex(Position(dx, y_bot), Angle(0.0)),
                Vertex(Position(-dx, y_bot), Angle(0.0)),
                Vertex(Position(-dx, y_top), Angle(0.0)),
            ],
        )
    )

    # Switches
    switch_dx = 1.5
    switch_dy = 0.9
    for circuit in range(1, circuits + 1):
        y = pin1_y - (circuit - 1) * 2.54
        if variant == VARIANT_EU:
            symbol.add_polygon(
                Polygon(
                    _uuid(f'polygon-switch-{circuit:02}-left'),
                    Layer('sym_outlines'),
                    Width(0.15875),
                    Fill(False),
                    GrabArea(False),
                    [
                        Vertex(Position(-dx, y), Angle(0.0)),
                        Vertex(Position(-switch_dx, y), Angle(0.0)),
                        Vertex(Position(switch_dx + 0.15, y + switch_dy), Angle(0.0)),
                    ],
                )
            )
            symbol.add_polygon(
                Polygon(
                    _uuid(f'polygon-switch-{circuit:02}-right'),
                    Layer('sym_outlines'),
                    Width(0.15875),
                    Fill(False),
                    GrabArea(False),
                    [
                        Vertex(Position(switch_dx, y + 0.2), Angle(0.0)),
                        Vertex(Position(switch_dx, y), Angle(0.0)),
                        Vertex(Position(dx, y), Angle(0.0)),
                    ],
                )
            )
        elif variant == VARIANT_US:
            circle_dia = 0.9
            for sign, side in [(-1, 'left'), (1, 'right')]:
                symbol.add_circle(
                    Circle(
                        _uuid(f'circle-switch-{circuit:02}-{side}'),
                        Layer('sym_outlines'),
                        Width(0.2),
                        Fill(False),
                        GrabArea(False),
                        Diameter(circle_dia),
                        Position(sign * switch_dx, y),
                    )
                )
                symbol.add_polygon(
                    Polygon(
                        _uuid(f'polygon-switch-{circuit:02}-{side}'),
                        Layer('sym_outlines'),
                        Width(0.15875),
                        Fill(False),
                        GrabArea(False),
                        [
                            Vertex(Position(sign * dx, y), Angle(0.0)),
                            Vertex(Position(sign * (switch_dx + circle_dia / 2), y), Angle(0.0)),
                        ],
                    )
                )
            symbol.add_polygon(
                Polygon(
                    _uuid(f'polygon-switch-{circuit:02}-contact'),
                    Layer('sym_outlines'),
                    Width(0.2),
                    Fill(False),
                    GrabArea(False),
                    [
                        Vertex(Position(-switch_dx + circle_dia / 2, y + 0.2), Angle(0.0)),
                        Vertex(
                            Position(switch_dx + 0.2, y + switch_dy + (circle_dia / 2) - 0.1),
                            Angle(0.0),
                        ),
                    ],
                )
            )
        else:
            raise Exception('Unknown variant')

    # Name
    symbol.add_text(
        Text(
            _uuid('text-name'),
            Layer('sym_names'),
            Value('{{NAME}}'),
            Align('left bottom'),
            Height(2.5),
            Position(-dx, y_top),
            Rotation(0.0),
        )
    )

    # Value
    symbol.add_text(
        Text(
            _uuid('text-value'),
            Layer('sym_values'),
            Value('{{VALUE}}'),
            Align('left top'),
            Height(2.5),
            Position(-dx, y_bot),
            Rotation(0.0),
        )
    )

    symbol.serialize(path.join('out', library, 'sym'))


def generate_cmp(
    library: str,
    author: str,
    name: str,
    cmpcat: str,
    keywords: str,
    circuits: int,
    version: str,
    create_date: Optional[str] = None,
) -> None:
    full_name = name.format(circuits=circuits)

    def _uuid(identifier: str) -> str:
        return uuid('cmp', f'{circuits:02}', identifier)

    uuid_cmp = _uuid('cmp')

    print('Generating {}: {}'.format(full_name, uuid_cmp))

    # Component
    component = Component(
        uuid=uuid_cmp,
        name=Name(full_name),
        description=Description(
            f'DIP switch array with {circuits} circuits.\n\nGenerated with {generator}'
        ),
        keywords=Keywords(keywords),
        author=Author(author),
        version=Version(version),
        created=Created(create_date or now()),
        deprecated=Deprecated(False),
        generated_by=GeneratedBy(''),
        categories=[Category(cmpcat)],
        schematic_only=SchematicOnly(False),
        default_value=DefaultValue('{{MPN or DEVICE}}'),
        prefix=Prefix('S'),
    )

    # Signals
    for circuit in range(1, circuits + 1):
        for letter in ['a', 'b']:
            component.add_signal(
                Signal(
                    _uuid(f'signal-{circuit:02}{letter}'),
                    Name(f'{circuit}{letter.upper()}'),
                    Role.PASSIVE,
                    Required(False),
                    Negated(False),
                    Clock(False),
                    ForcedNet(''),
                )
            )

    # Default variant
    for variant in [VARIANT_EU, VARIANT_US]:
        gate = Gate(
            _uuid(f'combined-{variant.id}-gate'),
            SymbolUUID(uuid_cache[f'sym-{variant.id}-{circuits:02}-sym']),
            Position(0, 0),
            Rotation(0),
            Required(True),
            Suffix(''),
        )
        for circuit in range(1, circuits + 1):
            for letter in ['a', 'b']:
                pin_uuid = uuid_cache[f'sym-{variant.id}-{circuits:02}-pin-{circuit:02}{letter}']
                sig_uuid = uuid_cache[f'cmp-{circuits:02}-signal-{circuit:02}{letter}']
                display_number = (circuits > 1) and (letter == 'a')
                gate.add_pin_signal_map(
                    PinSignalMap(
                        pin_uuid,
                        SignalUUID(sig_uuid),
                        TextDesignator.SYMBOL_PIN_NAME if display_number else TextDesignator.NONE,
                    )
                )
        component.add_variant(
            Variant(
                _uuid(f'combined-{variant.id}-variant'),
                Norm(variant.norm),
                Name(f'Combined, {variant.description}'),
                Description(''),
                gate,
            )
        )

    # Split variant
    if circuits > 1:
        for variant in [VARIANT_EU, VARIANT_US]:
            cmp_variant = Variant(
                _uuid(f'split-{variant.id}-variant'),
                Norm(variant.norm),
                Name(f'Split, {variant.description}'),
                Description(''),
            )
            component.add_variant(cmp_variant)
            spacing = 2.54 * 4
            y0 = spacing * (circuits // 2)
            for circuit in range(1, circuits + 1):
                gate = Gate(
                    _uuid(f'split-{variant.id}-gate-{circuit:02}'),
                    SymbolUUID(uuid_cache[f'sym-{variant.id}-01-sym']),
                    Position(0, y0 - (circuit - 1) * spacing),
                    Rotation(0),
                    Required(True),
                    Suffix(str(circuit)),
                )
                for letter in ['a', 'b']:
                    pin_uuid = uuid_cache[f'sym-{variant.id}-01-pin-01{letter}']
                    sig_uuid = uuid_cache[f'cmp-{circuits:02}-signal-{circuit:02}{letter}']
                    gate.add_pin_signal_map(
                        PinSignalMap(
                            pin_uuid,
                            SignalUUID(sig_uuid),
                            TextDesignator.NONE,
                        )
                    )
                cmp_variant.add_gate(gate)

    component.serialize(path.join('out', library, 'cmp'))


def generate_pkg(
    library: str,
    author: str,
    version: str,
    create_date: Optional[str],
    family: Family,
    model: Model,
    generate_3d_models: bool,
) -> None:
    full_name = family.pkg_name_prefix + '_' + model.name.replace(' ', '_')

    def _uuid(identifier: str) -> str:
        return uuid('pkg', model.uuid_key(family), identifier)

    uuid_pkg = _uuid('pkg')

    print('Generating {}: {}'.format(full_name, uuid_pkg))

    package = Package(
        uuid=uuid_pkg,
        name=Name(full_name),
        description=Description(model.get_description(family)),
        keywords=Keywords(model.get_keywords(family)),
        author=Author(author),
        version=Version(version),
        created=Created(create_date or now()),
        deprecated=Deprecated(False),
        generated_by=GeneratedBy(''),
        categories=[
            Category('194951ec-03dd-412a-9828-70c40bbdd22d'),
            Category('c0f16db0-f0db-4121-ab12-b4570ff79738'),
        ],
        assembly_type=AssemblyType.THT
        if isinstance(family.lead_config, ThtLeadConfig)
        else AssemblyType.SMT,
    )

    # Footprint
    footprint = Footprint(
        uuid=_uuid('footprint'),
        name=Name('default'),
        description=Description(''),
        position_3d=Position3D.zero(),
        rotation_3d=Rotation3D.zero(),
    )
    package.add_footprint(footprint)

    # Pads
    for i in range(model.circuits * 2):
        uuid_pkg_pad = _uuid('pad-{}'.format(i + 1))
        package.add_pad(PackagePad(uuid=uuid_pkg_pad, name=Name(str(i + 1))))
        uuid_fpt_pad = _uuid('default-pad-{}'.format(i + 1))
        x = (family.lead_config.pitch_x / 2) * (-1 if (i < model.circuits) else 1)
        y = get_y(i, model.circuits, family.lead_config.pitch_y)
        if isinstance(family.lead_config, ThtLeadConfig):
            footprint.add_pad(
                FootprintPad(
                    uuid=uuid_fpt_pad,
                    side=ComponentSide.TOP,
                    shape=Shape.ROUNDED_RECT,
                    position=Position(x, y),
                    rotation=Rotation(0),
                    size=Size(family.lead_config.pad_diameter, family.lead_config.pad_diameter),
                    radius=ShapeRadius(0.0 if (i == 0) else 1.0),
                    stop_mask=StopMaskConfig(StopMaskConfig.AUTO),
                    solder_paste=SolderPasteConfig.OFF,
                    copper_clearance=CopperClearance(0),
                    function=PadFunction.STANDARD_PAD,
                    package_pad=PackagePadUuid(uuid_pkg_pad),
                    holes=[
                        PadHole(
                            uuid_fpt_pad,
                            DrillDiameter(family.lead_config.drill),
                            [Vertex(Position(0.0, 0.0), Angle(0.0))],
                        )
                    ],
                )
            )
        else:
            footprint.add_pad(
                FootprintPad(
                    uuid=uuid_fpt_pad,
                    side=ComponentSide.TOP,
                    shape=Shape.ROUNDED_RECT,
                    position=Position(x, y),
                    rotation=Rotation(0),
                    size=Size(family.lead_config.pad_size_x, family.lead_config.pad_size_y),
                    radius=ShapeRadius(0.5),
                    stop_mask=StopMaskConfig(StopMaskConfig.AUTO),
                    solder_paste=SolderPasteConfig.AUTO,
                    copper_clearance=CopperClearance(0),
                    function=PadFunction.STANDARD_PAD,
                    package_pad=PackagePadUuid(uuid_pkg_pad),
                    holes=[],
                )
            )
        if isinstance(family.lead_config, GullWingLeadConfig):
            left = (family.lead_config.span / 2) * (-1 if (i % 2 == 0) else 1)
            right = (family.body_size_x / 2) * (-1 if (i % 2 == 0) else 1)
            top = y + (family.lead_config.width / 2)
            bottom = y - (family.lead_config.width / 2)
            footprint.add_polygon(
                Polygon(
                    uuid=_uuid('default-polygon-documentation-{}'.format(i + 1)),
                    layer=Layer('top_documentation'),
                    width=Width(0),
                    fill=Fill(True),
                    grab_area=GrabArea(False),
                    vertices=[
                        Vertex(Position(left, top), Angle(0)),
                        Vertex(Position(right, top), Angle(0)),
                        Vertex(Position(right, bottom), Angle(0)),
                        Vertex(Position(left, bottom), Angle(0)),
                        Vertex(Position(left, top), Angle(0)),
                    ],
                )
            )

    # Documentation outline
    line_width = 0.2
    top = (model.body_size_y / 2) - (line_width / 2)
    bottom = -top
    left = -(family.body_size_x / 2) + (line_width / 2)
    right = -left
    footprint.add_polygon(
        Polygon(
            uuid=_uuid('default-polygon-documentation'),
            layer=Layer('top_documentation'),
            width=Width(line_width),
            fill=Fill(False),
            grab_area=GrabArea(False),
            vertices=[
                Vertex(Position(left, top), Angle(0)),
                Vertex(Position(right, top), Angle(0)),
                Vertex(Position(right, bottom), Angle(0)),
                Vertex(Position(left, bottom), Angle(0)),
                Vertex(Position(left, top), Angle(0)),
            ],
        )
    )

    # Documentation actuators
    window_dx = family.window_size[0] / 2
    window_dy = family.window_size[1] / 2
    window_width = 0.1
    actuator_dy = family.actuator_size / 2
    actuator_x0 = (-window_dx / 2) - actuator_dy
    actuator_x1 = actuator_x0 + family.actuator_size
    text_x = -family.lead_config.pitch_x / 2
    if isinstance(family.lead_config, ThtLeadConfig):
        text_x += family.lead_config.pad_diameter / 2
    else:
        text_x += family.lead_config.pad_size_x / 2
    text_x = (text_x + (-window_dx - (line_width / 2))) / 2
    for circuit in range(model.circuits):
        y = get_y(circuit, model.circuits, family.lead_config.pitch_y)
        footprint.add_polygon(
            Polygon(
                uuid=_uuid(f'default-polygon-documentation-window-{circuit}'),
                layer=Layer('top_documentation'),
                width=Width(window_width),
                fill=Fill(False),
                grab_area=GrabArea(False),
                vertices=[
                    Vertex(Position(-window_dx, y + window_dy), Angle(0)),
                    Vertex(Position(window_dx, y + window_dy), Angle(0)),
                    Vertex(Position(window_dx, y - window_dy), Angle(0)),
                    Vertex(Position(-window_dx, y - window_dy), Angle(0)),
                    Vertex(Position(-window_dx, y + window_dy), Angle(0)),
                ],
            )
        )
        footprint.add_polygon(
            Polygon(
                uuid=_uuid(f'default-polygon-documentation-actuator-{circuit}'),
                layer=Layer('top_documentation'),
                width=Width(0),
                fill=Fill(True),
                grab_area=GrabArea(False),
                vertices=[
                    Vertex(Position(actuator_x0, y + actuator_dy), Angle(0)),
                    Vertex(Position(actuator_x1, y + actuator_dy), Angle(0)),
                    Vertex(Position(actuator_x1, y - actuator_dy), Angle(0)),
                    Vertex(Position(actuator_x0, y - actuator_dy), Angle(0)),
                    Vertex(Position(actuator_x0, y + actuator_dy), Angle(0)),
                ],
            )
        )
        footprint.add_text(
            StrokeText(
                uuid=_uuid(f'default-text-documentation-{circuit}'),
                layer=Layer('top_documentation'),
                height=Height(0.8),
                stroke_width=StrokeWidth(0.1),
                letter_spacing=LetterSpacing.AUTO,
                line_spacing=LineSpacing.AUTO,
                align=Align('center center'),
                position=Position(text_x, y),
                rotation=Rotation(-90.0),
                auto_rotate=AutoRotate(False),
                mirror=Mirror(False),
                value=Value(f'{circuit + 1}'),
            )
        )

    # Legend outline top & bottom
    dx = (family.body_size_x / 2) + (line_width / 2)
    dx_pin1 = (family.lead_config.pitch_x / 2) - (line_width / 2)
    dy = (model.body_size_y / 2) + (line_width / 2)
    dy_inner = get_y(0, model.circuits, family.lead_config.pitch_y)
    if isinstance(family.lead_config, ThtLeadConfig):
        dx_pin1 += family.lead_config.pad_diameter / 2
        dy_inner += (family.lead_config.pad_diameter / 2) + (line_width / 2) + 0.15
    else:
        dx_pin1 += family.lead_config.pad_size_x / 2
        dy_inner += (family.lead_config.pad_size_y / 2) + (line_width / 2) + 0.15
    for sign, name in [(1, 'top'), (-1, 'bottom')]:
        pin1_vertices = [Vertex(Position(-dx_pin1, dy_inner * sign), Angle(0))]
        footprint.add_polygon(
            Polygon(
                uuid=_uuid('default-polygon-legend-{}'.format(name)),
                layer=Layer('top_legend'),
                width=Width(line_width),
                fill=Fill(False),
                grab_area=GrabArea(False),
                vertices=(pin1_vertices if (sign > 0) else [])
                + [
                    Vertex(Position(-dx, dy_inner * sign), Angle(0)),
                    Vertex(Position(-dx, dy * sign), Angle(0)),
                    Vertex(Position(dx, dy * sign), Angle(0)),
                    Vertex(Position(dx, dy_inner * sign), Angle(0)),
                ],
            )
        )

    # Package outline
    top = model.body_size_y / 2
    bottom = -top
    left = -(family.body_size_x / 2)
    right = -left
    if isinstance(family.lead_config, GullWingLeadConfig):
        left_leads = -(family.lead_config.span / 2)
        right_leads = -left_leads
        leads_dy = family.lead_config.width / 2
        outline_vertices = [
            Vertex(Position(left, top), Angle(0)),
            Vertex(Position(right, top), Angle(0)),
        ]
        for i in range(model.circuits):
            y = get_y(model.circuits * 2 - i - 1, model.circuits, family.lead_config.pitch_y)
            outline_vertices += [
                Vertex(Position(right, y + leads_dy), Angle(0)),
                Vertex(Position(right_leads, y + leads_dy), Angle(0)),
                Vertex(Position(right_leads, y - leads_dy), Angle(0)),
                Vertex(Position(right, y - leads_dy), Angle(0)),
            ]
        outline_vertices += [
            Vertex(Position(right, bottom), Angle(0)),
            Vertex(Position(left, bottom), Angle(0)),
        ]
        for i in range(model.circuits):
            y = get_y(model.circuits - i - 1, model.circuits, family.lead_config.pitch_y)
            outline_vertices += [
                Vertex(Position(left, y - leads_dy), Angle(0)),
                Vertex(Position(left_leads, y - leads_dy), Angle(0)),
                Vertex(Position(left_leads, y + leads_dy), Angle(0)),
                Vertex(Position(left, y + leads_dy), Angle(0)),
            ]
    else:
        outline_vertices = [
            Vertex(Position(left, top), Angle(0)),
            Vertex(Position(right, top), Angle(0)),
            Vertex(Position(right, bottom), Angle(0)),
            Vertex(Position(left, bottom), Angle(0)),
        ]
    footprint.add_polygon(
        Polygon(
            uuid=_uuid('default-polygon-outline'),
            layer=Layer('top_package_outlines'),
            width=Width(0),
            fill=Fill(False),
            grab_area=GrabArea(False),
            vertices=outline_vertices,
        )
    )

    # Courtyard
    courtyard_excess = 0.4
    top = (model.body_size_y / 2) + courtyard_excess
    bottom = -top
    left = -(family.body_size_x / 2) - courtyard_excess
    right = -left
    if isinstance(family.lead_config, GullWingLeadConfig):
        top_leads = (
            get_y(0, model.circuits, family.lead_config.pitch_y)
            + (family.lead_config.width / 2)
            + courtyard_excess
        )
        bottom_leads = -top_leads
        left_leads = -(family.lead_config.span / 2) - courtyard_excess
        right_leads = -left_leads
        courtyard_vertices = [
            Vertex(Position(left, top), Angle(0)),
            Vertex(Position(right, top), Angle(0)),
            Vertex(Position(right, top_leads), Angle(0)),
            Vertex(Position(right_leads, top_leads), Angle(0)),
            Vertex(Position(right_leads, bottom_leads), Angle(0)),
            Vertex(Position(right, bottom_leads), Angle(0)),
            Vertex(Position(right, bottom), Angle(0)),
            Vertex(Position(left, bottom), Angle(0)),
            Vertex(Position(left, bottom_leads), Angle(0)),
            Vertex(Position(left_leads, bottom_leads), Angle(0)),
            Vertex(Position(left_leads, top_leads), Angle(0)),
            Vertex(Position(left, top_leads), Angle(0)),
        ]
    else:
        courtyard_vertices = [
            Vertex(Position(left, top), Angle(0)),
            Vertex(Position(right, top), Angle(0)),
            Vertex(Position(right, bottom), Angle(0)),
            Vertex(Position(left, bottom), Angle(0)),
        ]
    footprint.add_polygon(
        Polygon(
            uuid=_uuid('default-polygon-courtyard'),
            layer=Layer('top_courtyard'),
            width=Width(0),
            fill=Fill(False),
            grab_area=GrabArea(False),
            vertices=courtyard_vertices,
        )
    )

    # Labels
    top = (model.body_size_y / 2) + line_width
    bottom = -top
    footprint.add_text(
        StrokeText(
            uuid=_uuid('default-text-name'),
            layer=Layer('top_names'),
            height=Height(1.0),
            stroke_width=StrokeWidth(0.2),
            letter_spacing=LetterSpacing.AUTO,
            line_spacing=LineSpacing.AUTO,
            align=Align('center bottom'),
            position=Position(0.0, top + 0.4),
            rotation=Rotation(0.0),
            auto_rotate=AutoRotate(True),
            mirror=Mirror(False),
            value=Value('{{NAME}}'),
        )
    )
    footprint.add_text(
        StrokeText(
            uuid=_uuid('default-text-value'),
            layer=Layer('top_values'),
            height=Height(1.0),
            stroke_width=StrokeWidth(0.2),
            letter_spacing=LetterSpacing.AUTO,
            line_spacing=LineSpacing.AUTO,
            align=Align('center top'),
            position=Position(0.0, bottom - 0.4),
            rotation=Rotation(0.0),
            auto_rotate=AutoRotate(True),
            mirror=Mirror(False),
            value=Value('{{VALUE}}'),
        )
    )

    # Generate 3D model
    uuid_3d = _uuid('3d')
    if generate_3d_models:
        generate_3d_model(library, full_name, uuid_pkg, uuid_3d, family, model)
    package.add_3d_model(Package3DModel(uuid_3d, Name(full_name)))
    for footprint in package.footprints:
        footprint.add_3d_model(Footprint3DModel(uuid_3d))

    package.serialize(path.join('out', library, 'pkg'))


def generate_3d_model(
    library: str,
    full_name: str,
    uuid_pkg: str,
    uuid_3d: str,
    family: Family,
    model: Model,
) -> None:
    import cadquery as cq

    from cadquery_helpers import StepAssembly, StepColor

    print(f'Generating pkg 3D model "{full_name}": {uuid_3d}')

    bend_radius = 0.3

    body = (
        cq.Workplane('XY', origin=(0, 0, family.body_standoff))
        .box(
            family.body_size_x, model.body_size_y, family.body_size_z, centered=(True, True, False)
        )
        .edges()
        .fillet(0.2)
    )
    for i in range(model.circuits):
        y = get_y(i, model.circuits, family.lead_config.pitch_y)
        body = body.workplane(origin=(0, y), offset=family.body_size_z / 2).box(
            family.window_size[0],
            family.window_size[1],
            2.0,
            centered=(True, True, True),
            combine='cut',
        )
    actuator_x = -family.window_size[0] / 4
    actuator = cq.Workplane(
        'XY', origin=(actuator_x, 0, family.body_standoff + family.body_size_z - 1.0)
    ).box(
        family.actuator_size,
        family.actuator_size,
        family.actuator_height + 1.0,
        centered=(True, True, False),
    )
    inner = cq.Workplane('XY', origin=(0, 0, family.body_standoff + family.body_size_z - 1.0)).box(
        family.window_size[0] + 0.5, model.body_size_y - 0.5, 0.2, centered=(True, True, True)
    )
    if isinstance(family.lead_config, ThtLeadConfig):
        lead_height = family.lead_config.length + family.body_standoff + 0.5
        lead_path = (
            cq.Workplane('XZ')
            .lineTo(0.0, lead_height)
            .ellipseArc(x_radius=bend_radius, y_radius=bend_radius, angle1=90, angle2=180, sense=-1)
            .lineTo(family.lead_config.pitch_x - bend_radius, lead_height + bend_radius)
            .ellipseArc(x_radius=bend_radius, y_radius=bend_radius, angle1=0, angle2=90, sense=-1)
            .lineTo(family.lead_config.pitch_x, 0.0)
        )
        lead = (
            cq.Workplane('XY')
            .rect(family.lead_config.thickness, family.lead_config.width_top)
            .sweep(lead_path)
        )
        lead_cutout_width = (family.lead_config.width_top - family.lead_config.width_bottom) / 2
        lead = (
            lead.faces('>X')
            .workplane()
            .lineTo(-family.lead_config.width_bottom / 2, 0)
            .lineTo(-family.lead_config.width_bottom / 2, family.lead_config.length)
            .lineTo(
                -family.lead_config.width_top * 0.51, family.lead_config.length + lead_cutout_width
            )
            .lineTo(-family.lead_config.width_top, -1)
            .lineTo(family.lead_config.width_top, -1)
            .lineTo(
                family.lead_config.width_top * 0.51, family.lead_config.length + lead_cutout_width
            )
            .lineTo(family.lead_config.width_bottom / 2, family.lead_config.length)
            .lineTo(family.lead_config.width_bottom / 2, 0)
            .close()
            .cutThruAll()
        )
        lead_xz = (-family.lead_config.pitch_x / 2, -family.lead_config.length)
    elif isinstance(family.lead_config, GullWingLeadConfig):
        contact_length = (
            ((family.lead_config.span - family.body_size_x) / 2)
            - bend_radius
            - family.lead_config.thickness
        )
        lead_height = family.body_standoff + 0.3
        lead_path = (
            cq.Workplane('XZ')
            .lineTo(contact_length, 0.0)
            .ellipseArc(x_radius=bend_radius, y_radius=bend_radius, angle1=-90, angle2=360, sense=1)
            .lineTo(contact_length + bend_radius, 0.2 + bend_radius + lead_height)
            .ellipseArc(x_radius=bend_radius, y_radius=bend_radius, angle1=90, angle2=180, sense=-1)
            .lineTo(
                family.lead_config.span - contact_length - 2 * bend_radius,
                0.2 + 2 * bend_radius + lead_height,
            )
            .ellipseArc(x_radius=bend_radius, y_radius=bend_radius, angle1=0, angle2=90, sense=-1)
            .lineTo(family.lead_config.span - contact_length - bend_radius, bend_radius)
            .ellipseArc(
                x_radius=bend_radius, y_radius=bend_radius, angle1=-180, angle2=270, sense=1
            )
            .lineTo(family.lead_config.span, 0.0)
        )
        lead = (
            cq.Workplane('ZY')
            .rect(family.lead_config.thickness, family.lead_config.width)
            .sweep(lead_path)
        )
        lead_xz = (-family.lead_config.span / 2, family.lead_config.thickness / 2)

    assembly = StepAssembly(full_name)
    assembly.add_body(body, 'body', StepColor.IC_BODY)
    assembly.add_body(inner, 'inner', cq.Color('gray56'))
    for i in range(model.circuits):
        assembly.add_body(
            lead,
            'lead-{}'.format(i + 1),
            StepColor.LEAD_SMT,
            location=cq.Location(
                (lead_xz[0], get_y(i, model.circuits, family.lead_config.pitch_y), lead_xz[1])
            ),
        )
        assembly.add_body(
            actuator,
            'actuator-{}'.format(i + 1),
            cq.Color(family.actuator_color),
            location=cq.Location((0, get_y(i, model.circuits, family.lead_config.pitch_y), 0)),
        )

    # Save without fusing for massively better minification!
    out_path = path.join('out', library, 'pkg', uuid_pkg, f'{uuid_3d}.step')
    assembly.save(out_path, fused=False)


def generate_dev(
    library: str,
    author: str,
    version: str,
    create_date: Optional[str],
    family: Family,
    model: Model,
) -> None:
    full_name = f'{family.dev_name_prefix} {model.name}'

    def _uuid(identifier: str) -> str:
        return uuid('dev', model.uuid_key(family), identifier)

    uuid_dev = _uuid('dev')

    print('Generating {}: {}'.format(full_name, uuid_dev))

    device = Device(
        uuid=uuid_dev,
        name=Name(full_name),
        description=Description(model.get_description(family)),
        keywords=Keywords(model.get_keywords(family)),
        author=Author(author),
        version=Version(version),
        created=Created(create_date or now()),
        deprecated=Deprecated(False),
        generated_by=GeneratedBy(''),
        categories=[Category('e29f0cb3-ef6d-4203-b854-d75150cbae0b')],
        component_uuid=ComponentUUID(uuid_cache[f'cmp-{model.circuits:02}-cmp']),
        package_uuid=PackageUUID(uuid_cache['pkg-' + model.uuid_key(family) + '-pkg']),
    )

    for pad in range(1, (model.circuits * 2) + 1):
        circuit = pad if (pad <= model.circuits) else ((model.circuits * 2) + 1 - pad)
        letter = 'a' if (pad <= model.circuits) else 'b'
        signal_uuid = uuid_cache[f'cmp-{model.circuits:02}-signal-{circuit:02}{letter}']
        pad_uuid = uuid_cache[f'pkg-{model.uuid_key(family)}-pad-{pad}']
        device.add_pad(ComponentPad(pad_uuid, SignalUUID(signal_uuid)))

    for part in model.parts:
        part.attributes = model.common_part_attributes + part.attributes
        device.add_part(part)

    if family.datasheet:
        device.add_resource(
            Resource(
                name='Datasheet {}'.format(family.datasheet_name),
                mediatype='application/pdf',
                url=family.datasheet,
            )
        )

    device.serialize(path.join('out', library, 'dev'))


if __name__ == '__main__':
    if '--help' in sys.argv or '-h' in sys.argv:
        print(f'Usage: {sys.argv[0]} [--3d]')
        print()
        print('Options:')
        print('  --3d    Generate 3D models using cadquery')
        sys.exit(1)

    generate_3d_models = '--3d' in sys.argv
    if not generate_3d_models:
        warning = 'Note: Not generating 3D models unless the "--3d" argument is passed in!'
        print(f'\033[1;33m{warning}\033[0m')

    # Symbols & Components
    for i in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14]:
        generate_sym(
            library='LibrePCB_Base.lplib',
            author='Urban B.',
            name='DIP Switch {circuits}x {variant.name}',
            cmpcat='e29f0cb3-ef6d-4203-b854-d75150cbae0b',
            keywords='slide',
            circuits=i,
            version='0.1',
            variant=VARIANT_EU,
            create_date='2025-10-11T14:33:06Z',
        )
        generate_sym(
            library='LibrePCB_Base.lplib',
            author='Urban B.',
            name='DIP Switch {circuits}x {variant.name}',
            cmpcat='e29f0cb3-ef6d-4203-b854-d75150cbae0b',
            keywords='slide',
            circuits=i,
            version='0.1',
            variant=VARIANT_US,
            create_date='2025-10-11T14:33:06Z',
        )
        generate_cmp(
            library='LibrePCB_Base.lplib',
            author='Urban B.',
            name='DIP Switch {circuits}x',
            cmpcat='e29f0cb3-ef6d-4203-b854-d75150cbae0b',
            keywords='slide',
            circuits=i,
            version='0.1',
            create_date='2025-10-11T14:33:06Z',
        )

    # C&K SDA series
    for actuator in ['H0', 'H1']:  # Flush, Extended
        for terminations in ['', 'S']:  # Thru-hole, Gull wing
            if terminations == '':
                family = Family(
                    manufacturer='C&K',
                    pkg_name_prefix='CK',
                    dev_name_prefix='C&K',
                    body_size_x=7.49,
                    body_size_z=3.5,
                    body_standoff=4.65 - 3.5,
                    window_size=(2.8, 1.4),  # guessed
                    actuator_size=1.0,  # guessed
                    actuator_height=1.0 if (actuator == 'H1') else 0.0,
                    actuator_color='gray97',
                    lead_config=ThtLeadConfig(
                        pitch_x=7.62,
                        pitch_y=2.54,
                        drill=0.8,
                        pad_diameter=1.5,
                        thickness=0.25,
                        width_top=1.6,
                        width_bottom=0.61,
                        length=2.7,
                    ),
                    datasheet='https://www.ckswitches.com/media/1327/sda.pdf',
                    datasheet_name='SDA Series',
                    keywords=['c&k'],
                )
            elif terminations == 'S':
                family = Family(
                    manufacturer='C&K',
                    pkg_name_prefix='CK',
                    dev_name_prefix='C&K',
                    body_size_x=7.49,
                    body_size_z=4.45 - 0.8,
                    body_standoff=0.8,
                    window_size=(2.8, 1.4),  # guessed
                    actuator_size=1.0,  # guessed
                    actuator_height=1.0 if (actuator == 'H1') else 0.0,
                    actuator_color='gray97',
                    lead_config=GullWingLeadConfig(
                        pitch_x=8.25,
                        pitch_y=2.54,
                        pad_size_x=2.15,
                        pad_size_y=1.5,
                        thickness=0.3,  # not documented
                        width=0.61,
                        span=9.3,
                    ),
                    datasheet='https://www.ckswitches.com/media/1327/sda.pdf',
                    datasheet_name='SDA Series',
                    keywords=['c&k'],
                )
            for circuits in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12]:
                parts = []
                parts.append(
                    Part(
                        f'SDA{circuits:02}{actuator}{terminations}B',
                        Manufacturer('C&K'),
                        [
                            Attribute('FEATURES', 'Sealed', AttributeType.STRING, None),
                            Attribute('PACKAGING', 'Tube', AttributeType.STRING, None),
                        ],
                    )
                )
                if terminations == 'S':
                    parts.append(
                        Part(
                            f'SDA{circuits:02}{actuator}{terminations}BR',
                            Manufacturer('C&K'),
                            [
                                Attribute('FEATURES', 'Sealed', AttributeType.STRING, None),
                                Attribute('PACKAGING', 'T&R', AttributeType.STRING, None),
                            ],
                        )
                    )
                parts.append(
                    Part(
                        f'SDA{circuits:02}{actuator}{terminations}BD',
                        Manufacturer('C&K'),
                        [
                            Attribute('PACKAGING', 'Tube', AttributeType.STRING, None),
                        ],
                    )
                )
                if terminations == 'S':
                    parts.append(
                        Part(
                            f'SDA{circuits:02}{actuator}{terminations}BDR',
                            Manufacturer('C&K'),
                            [
                                Attribute('PACKAGING', 'T&R', AttributeType.STRING, None),
                            ],
                        )
                    )
                model = Model(
                    name=f'SDA{circuits:02}{actuator}{terminations}B',
                    circuits=circuits,
                    body_size_y=1.98 + 2.54 * circuits,
                    parts=parts,
                )
                generate_pkg(
                    library='CK.lplib',
                    author='U. Bruhin',
                    version='0.1',
                    create_date='2025-11-11T15:12:42Z',
                    family=family,
                    model=model,
                    generate_3d_models=generate_3d_models,
                )
                generate_dev(
                    library='CK.lplib',
                    author='U. Bruhin',
                    version='0.1',
                    create_date='2025-11-11T15:12:42Z',
                    family=family,
                    model=model,
                )

    save_cache(uuid_cache_file, uuid_cache)
