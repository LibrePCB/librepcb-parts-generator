"""
Generate various tactile switch packages & devices
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
    Name,
    Polygon,
    Position,
    Position3D,
    Resource,
    Rotation,
    Rotation3D,
    Value,
    Version,
    Vertex,
    Width,
)
from entities.component import SignalUUID
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

generator = 'librepcb-parts-generator (generate_tactile_switches.py)'

line_width = 0.2
courtyard_excess = 0.4


# Initialize UUID cache
uuid_cache_file = 'uuid_cache_tactile_switches.csv'
uuid_cache = init_cache(uuid_cache_file)


def uuid(category: str, full_name: str, identifier: str) -> str:
    key = '{}-{}-{}'.format(category, full_name, identifier).lower().replace(' ', '~')
    if key not in uuid_cache:
        uuid_cache[key] = str(uuid4())
    return uuid_cache[key]


class ThtLeadConfig:
    def __init__(
        self,
        pitch_x: float,
        pitch_y: float,
        drill: float,
        pad_diameter: float,
        thickness: float,
        width: float,
        length: float,
    ):
        self.pitch_x = pitch_x
        self.pitch_y = pitch_y
        self.drill = drill
        self.pad_diameter = pad_diameter
        self.thickness = thickness
        self.width = width
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


class JLeadConfig:
    def __init__(
        self,
        pitch_x: float,
        pitch_y: float,
        pad_size_x: float,
        pad_size_y: float,
        thickness: float,
        width: float,
    ):
        self.pitch_x = pitch_x
        self.pitch_y = pitch_y
        self.pad_size_x = pad_size_x
        self.pad_size_y = pad_size_y
        self.thickness = thickness
        self.width = width


class Family:
    def __init__(
        self,
        manufacturer: str,
        pkg_name_prefix: str,
        dev_name_prefix: str,
        body_size_x: float,
        body_size_y: float,
        body_size_z: float,
        actuator_size: Union[float, Tuple[float, float]],
        actuator_color: str,
        lead_config: Union[ThtLeadConfig, GullWingLeadConfig, JLeadConfig],
        datasheet: Optional[str],
        datasheet_name: Optional[str],
        keywords: List[str],
    ) -> None:
        self.manufacturer = manufacturer
        self.pkg_name_prefix = pkg_name_prefix
        self.dev_name_prefix = dev_name_prefix
        self.body_size_x = body_size_x
        self.body_size_y = body_size_y
        self.body_size_z = body_size_z
        self.actuator_size = actuator_size  # tuple=rectangular, float=circular
        self.actuator_color = actuator_color
        self.lead_config = lead_config
        self.datasheet = datasheet
        self.datasheet_name = datasheet_name
        self.keywords = keywords


class Model:
    def __init__(
        self,
        name: str,
        actuator_height: float,
        parts: List[Part],
        common_part_attributes: Optional[List[Attribute]] = None,
    ) -> None:
        self.name = name
        self.actuator_height = actuator_height  # From PCB surface to act. top
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
        s = f'Tactile switch from {family.manufacturer}.'
        s += f'\n\nBody Size: {family.body_size_x:.2f} x {family.body_size_y:.2f} mm'
        if isinstance(family.lead_config, ThtLeadConfig):
            s += f'\nPitch: {family.lead_config.pitch_x:.2f} x {family.lead_config.pitch_y:.2f} mm'
        if isinstance(family.lead_config, GullWingLeadConfig):
            s += f'\nLead Span: {family.lead_config.span:.2f} mm'
        if not isinstance(family.lead_config, ThtLeadConfig):
            s += f'\nLead Y-Pitch: {family.lead_config.pitch_y:.2f} mm'
        s += f'\nActuator Height: {self.actuator_height:.2f} mm'
        s += f'\n\nGenerated with {generator}'
        return s

    def get_keywords(self, family: Family) -> str:
        return ','.join(
            [
                'push',
                'press',
                'button',
                'switch',
                'tactile',
            ]
            + family.keywords
        )


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
    for i in range(4):
        uuid_pkg_pad = _uuid('pad-{}'.format(i + 1))
        package.add_pad(PackagePad(uuid=uuid_pkg_pad, name=Name(str(i + 1))))
        uuid_fpt_pad = _uuid('default-pad-{}'.format(i + 1))
        x = (family.lead_config.pitch_x / 2) * (-1 if (i % 2 == 0) else 1)
        y = (family.lead_config.pitch_y / 2) * (1 if (i < 2) else -1)
        if isinstance(family.lead_config, ThtLeadConfig):
            footprint.add_pad(
                FootprintPad(
                    uuid=uuid_fpt_pad,
                    side=ComponentSide.TOP,
                    shape=Shape.ROUNDED_RECT,
                    position=Position(x, y),
                    rotation=Rotation(0),
                    size=Size(family.lead_config.pad_diameter, family.lead_config.pad_diameter),
                    radius=ShapeRadius(1.0),
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
    top = (family.body_size_y / 2) - (line_width / 2)
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

    # Documentation actuator
    if isinstance(family.actuator_size, tuple):
        dx = family.actuator_size[0] / 2
        dy = family.actuator_size[1] / 2
        footprint.add_polygon(
            Polygon(
                uuid=_uuid('default-polygon-documentation-actuator'),
                layer=Layer('top_documentation'),
                width=Width(line_width),
                fill=Fill(False),
                grab_area=GrabArea(False),
                vertices=[
                    Vertex(Position(-dx, dy), Angle(0)),
                    Vertex(Position(dx, dy), Angle(0)),
                    Vertex(Position(dx, -dy), Angle(0)),
                    Vertex(Position(-dx, -dy), Angle(0)),
                    Vertex(Position(-dx, dy), Angle(0)),
                ],
            )
        )
    else:
        footprint.add_circle(
            Circle(
                uuid=_uuid('default-circle-documentation-actuator'),
                layer=Layer('top_documentation'),
                width=Width(line_width),
                fill=Fill(False),
                grab_area=GrabArea(False),
                diameter=Diameter(family.actuator_size - line_width),
                position=Position(0, 0),
            )
        )

    # Legend outline top & bottom
    dx = (family.body_size_x / 2) + (line_width / 2)
    dy = (family.body_size_y / 2) + (line_width / 2)
    if isinstance(family.lead_config, ThtLeadConfig):
        dx = min(
            dx,
            (family.lead_config.pitch_x / 2)
            - (family.lead_config.pad_diameter / 2)
            - (line_width / 2)
            - 0.15,
        )
    else:
        dx = min(
            dx,
            (family.lead_config.pitch_x / 2)
            - (family.lead_config.pad_size_x / 2)
            - (line_width / 2)
            - 0.15,
        )
    for sign, name in [(1, 'top'), (-1, 'bottom')]:
        footprint.add_polygon(
            Polygon(
                uuid=_uuid('default-polygon-legend-{}'.format(name)),
                layer=Layer('top_legend'),
                width=Width(line_width),
                fill=Fill(False),
                grab_area=GrabArea(False),
                vertices=[
                    Vertex(Position(-dx, dy * sign), Angle(0)),
                    Vertex(Position(dx, dy * sign), Angle(0)),
                ],
            )
        )

    # Legend outline left & right
    dx = (family.body_size_x / 2) + (line_width / 2)
    dy = (family.body_size_y / 2) + (line_width / 2)
    if isinstance(family.lead_config, ThtLeadConfig):
        dy = min(
            dy,
            (family.lead_config.pitch_y / 2)
            - (family.lead_config.pad_diameter / 2)
            - (line_width / 2)
            - 0.15,
        )
    else:
        dy = min(
            dy,
            (family.lead_config.pitch_y / 2)
            - (family.lead_config.pad_size_y / 2)
            - (line_width / 2)
            - 0.15,
        )
    for sign, name in [(-1, 'left'), (1, 'right')]:
        footprint.add_polygon(
            Polygon(
                uuid=_uuid('default-polygon-legend-{}'.format(name)),
                layer=Layer('top_legend'),
                width=Width(line_width),
                fill=Fill(False),
                grab_area=GrabArea(False),
                vertices=[
                    Vertex(Position(dx * sign, dy), Angle(0)),
                    Vertex(Position(dx * sign, -dy), Angle(0)),
                ],
            )
        )

    # Package outline
    top = family.body_size_y / 2
    bottom = -top
    left = -(family.body_size_x / 2)
    right = -left
    footprint.add_polygon(
        Polygon(
            uuid=_uuid('default-polygon-outline'),
            layer=Layer('top_package_outlines'),
            width=Width(0),
            fill=Fill(False),
            grab_area=GrabArea(False),
            vertices=[
                Vertex(Position(left, top), Angle(0)),
                Vertex(Position(right, top), Angle(0)),
                Vertex(Position(right, bottom), Angle(0)),
                Vertex(Position(left, bottom), Angle(0)),
            ],
        )
    )

    # Courtyard
    top = (family.body_size_y / 2) + courtyard_excess
    bottom = -top
    left = -(family.body_size_x / 2) - courtyard_excess
    right = -left
    footprint.add_polygon(
        Polygon(
            uuid=_uuid('default-polygon-courtyard'),
            layer=Layer('top_courtyard'),
            width=Width(0),
            fill=Fill(False),
            grab_area=GrabArea(False),
            vertices=[
                Vertex(Position(left, top), Angle(0)),
                Vertex(Position(right, top), Angle(0)),
                Vertex(Position(right, bottom), Angle(0)),
                Vertex(Position(left, bottom), Angle(0)),
            ],
        )
    )

    # Labels
    top = (family.body_size_y / 2) + line_width
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

    standoff = (family.lead_config.thickness) if (type(family.lead_config) is JLeadConfig) else 0.2
    bend_radius = 0.3

    body = (
        cq.Workplane('XY', origin=(0, 0, standoff))
        .box(
            family.body_size_x,
            family.body_size_y,
            family.body_size_z - standoff,
            centered=(True, True, False),
        )
        .edges()
        .fillet(0.2)
    )
    if isinstance(family.actuator_size, tuple):
        actuator = (
            cq.Workplane('XY', origin=(0, 0, 1.0))
            .box(
                family.actuator_size[0],
                family.actuator_size[1],
                model.actuator_height - 1.0,
                centered=(True, True, False),
            )
            .edges()
            .fillet(0.2)
        )
    else:
        actuator = (
            cq.Workplane('XY', origin=(0, 0, 1.0))
            .cylinder(
                model.actuator_height - 1.0, family.actuator_size / 2, centered=(True, True, False)
            )
            .edges()
            .fillet(0.2)
        )
    if isinstance(family.lead_config, ThtLeadConfig):
        lead_path = (
            cq.Workplane('XZ')
            .lineTo(0.0, 1.0)
            .lineTo(-0.5, 2.0)
            .lineTo(0.0, 3.0)
            .lineTo(0.0, 4.0)
            .ellipseArc(x_radius=bend_radius, y_radius=bend_radius, angle1=90, angle2=180, sense=-1)
            .lineTo(family.lead_config.pitch_x - bend_radius, 4.0 + bend_radius)
            .ellipseArc(x_radius=bend_radius, y_radius=bend_radius, angle1=0, angle2=90, sense=-1)
            .lineTo(family.lead_config.pitch_x, 3.0)
            .lineTo(family.lead_config.pitch_x + 0.5, 2.0)
            .lineTo(family.lead_config.pitch_x, 1.0)
            .lineTo(family.lead_config.pitch_x, 0.0)
        )
        lead = (
            cq.Workplane('XY')
            .rect(family.lead_config.thickness, family.lead_config.width)
            .sweep(lead_path)
        )
        lead_xz = (-family.lead_config.pitch_x / 2, -family.lead_config.length)
    elif isinstance(family.lead_config, GullWingLeadConfig):
        contact_length = (
            ((family.lead_config.span - family.body_size_x) / 2)
            - bend_radius
            - family.lead_config.thickness
        )
        lead_path = (
            cq.Workplane('XZ')
            .lineTo(contact_length, 0.0)
            .ellipseArc(x_radius=bend_radius, y_radius=bend_radius, angle1=-90, angle2=360, sense=1)
            .lineTo(contact_length + bend_radius, 0.2 + bend_radius)
            .ellipseArc(x_radius=bend_radius, y_radius=bend_radius, angle1=90, angle2=180, sense=-1)
            .lineTo(
                family.lead_config.span - contact_length - 2 * bend_radius, 0.2 + 2 * bend_radius
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
    elif isinstance(family.lead_config, JLeadConfig):
        width = family.body_size_x + family.lead_config.thickness
        height = 0.5
        contact_length = 0.4
        lead_path = (
            cq.Workplane('XZ')
            .lineTo(-contact_length, 0.0)
            .ellipseArc(
                x_radius=bend_radius, y_radius=bend_radius, angle1=180, angle2=270, sense=-1
            )
            .lineTo(-contact_length - bend_radius, height + bend_radius)
            .ellipseArc(x_radius=bend_radius, y_radius=bend_radius, angle1=90, angle2=180, sense=-1)
            .lineTo(width - contact_length - 2 * bend_radius, height + 2 * bend_radius)
            .ellipseArc(x_radius=bend_radius, y_radius=bend_radius, angle1=0, angle2=90, sense=-1)
            .lineTo(width - contact_length - bend_radius, bend_radius)
            .ellipseArc(x_radius=bend_radius, y_radius=bend_radius, angle1=-90, angle2=0, sense=-1)
            .lineTo(width - 2 * contact_length - 2 * bend_radius, 0.0)
        )
        lead = (
            cq.Workplane('ZY')
            .rect(family.lead_config.thickness, family.lead_config.width)
            .sweep(lead_path)
        )
        lead_xz = (-(width / 2) + contact_length + bend_radius, family.lead_config.thickness / 2)

    assembly = StepAssembly(full_name)
    assembly.add_body(body, 'body', StepColor.IC_BODY)
    assembly.add_body(actuator, 'actuator', cq.Color(family.actuator_color))
    assembly.add_body(
        lead,
        'lead-12',
        StepColor.LEAD_SMT,
        location=cq.Location((lead_xz[0], family.lead_config.pitch_y / 2, lead_xz[1])),
    )
    assembly.add_body(
        lead,
        'lead-34',
        StepColor.LEAD_SMT,
        location=cq.Location((lead_xz[0], -family.lead_config.pitch_y / 2, lead_xz[1])),
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
        component_uuid=ComponentUUID('6eedad0b-5b41-4233-9b7b-8be1ee8527e0'),
        package_uuid=PackageUUID(uuid('pkg', model.uuid_key(family), 'pkg')),
    )

    signal_uuids = [
        '33616b61-b981-452a-a672-e564bfabf6b1',
        '4c215f30-3492-4a32-94d3-7f3541afb7db',
    ]

    for i in range(4):
        pad_uuid = uuid('pkg', model.uuid_key(family), 'pad-{}'.format(i + 1))
        device.add_pad(ComponentPad(pad_uuid, SignalUUID(signal_uuids[i // 2])))

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

    # C&K PTS645Sxxx2LFS
    family = Family(
        manufacturer='C&K',
        pkg_name_prefix='CK',
        dev_name_prefix='C&K',
        body_size_x=6.0,
        body_size_y=6.0,
        body_size_z=3.45,
        actuator_size=3.5,  # round
        actuator_color='azure4',
        lead_config=ThtLeadConfig(
            pitch_x=6.5,
            pitch_y=4.5,
            drill=1.0,
            pad_diameter=1.7,
            thickness=0.3,
            width=0.7,
            length=3.0,
        ),
        datasheet='https://www.ckswitches.com/media/1471/pts645.pdf',
        datasheet_name='PTS645',
        keywords=[],
    )
    models = [
        # 4.3mm
        Model(
            name='PTS645Sx432',
            actuator_height=4.3,
            parts=[
                Part(
                    'PTS645SK432LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '260gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SL432LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '130gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SM432LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '160gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SN432LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '100gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SH432LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '200gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SP432LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '320gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SR432LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '360gf', AttributeType.STRING, None),
                    ],
                ),
            ],
            common_part_attributes=[
                Attribute('HEIGHT', '4.3mm', AttributeType.STRING, None),
            ],
        ),
        # 5.0mm
        Model(
            name='PTS645Sx502',
            actuator_height=5.0,
            parts=[
                Part(
                    'PTS645SK502LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '260gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SL502LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '130gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SM502LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '160gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SN502LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '100gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SH502LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '200gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SP502LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '320gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SR502LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '360gf', AttributeType.STRING, None),
                    ],
                ),
            ],
            common_part_attributes=[
                Attribute('HEIGHT', '5.0mm', AttributeType.STRING, None),
            ],
        ),
        # 7.0mm
        Model(
            name='PTS645Sx702',
            actuator_height=7.0,
            parts=[
                Part(
                    'PTS645SK702LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '260gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SL702LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '130gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SM702LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '160gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SN702LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '100gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SH702LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '200gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SP702LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '320gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SR702LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '360gf', AttributeType.STRING, None),
                    ],
                ),
            ],
            common_part_attributes=[
                Attribute('HEIGHT', '7.0mm', AttributeType.STRING, None),
            ],
        ),
        # 9.5mm
        Model(
            name='PTS645Sx952',
            actuator_height=9.5,
            parts=[
                Part(
                    'PTS645SK952LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '260gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SL952LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '130gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SM952LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '160gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SN952LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '100gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SH952LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '200gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SP952LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '320gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SR952LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '360gf', AttributeType.STRING, None),
                    ],
                ),
            ],
            common_part_attributes=[
                Attribute('HEIGHT', '9.5mm', AttributeType.STRING, None),
            ],
        ),
    ]
    for model in models:
        generate_pkg(
            library='CK.lplib',
            author='U. Bruhin',
            version='0.1',
            create_date='2025-04-15T21:39:13Z',
            family=family,
            model=model,
            generate_3d_models=generate_3d_models,
        )
        generate_dev(
            library='CK.lplib',
            author='U. Bruhin',
            version='0.1',
            create_date='2025-04-15T21:39:13Z',
            family=family,
            model=model,
        )

    # C&K PTS645SJxxx2LFS
    family = Family(
        manufacturer='C&K',
        pkg_name_prefix='CK',
        dev_name_prefix='C&K',
        body_size_x=6.0,
        body_size_y=6.0,
        body_size_z=3.45,
        actuator_size=(2.4, 2.4),  # rect
        actuator_color='azure4',
        lead_config=ThtLeadConfig(
            pitch_x=6.5,
            pitch_y=4.5,
            drill=1.0,
            pad_diameter=1.7,
            thickness=0.3,
            width=0.7,
            length=3.0,
        ),
        datasheet='https://www.ckswitches.com/media/1471/pts645.pdf',
        datasheet_name='PTS645',
        keywords=[],
    )
    models = [
        Model(
            name='PTS645SJx732',
            actuator_height=7.3,
            parts=[
                Part(
                    'PTS645SJK432LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '260gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SJL732LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '130gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SJM732LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '160gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SJN732LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '100gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SJH732LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '200gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SJP732LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '320gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SJR732LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '360gf', AttributeType.STRING, None),
                    ],
                ),
            ],
            common_part_attributes=[
                Attribute('HEIGHT', '7.3mm', AttributeType.STRING, None),
            ],
        ),
    ]
    for model in models:
        generate_pkg(
            library='CK.lplib',
            author='U. Bruhin',
            version='0.1',
            create_date='2025-04-15T21:39:13Z',
            family=family,
            model=model,
            generate_3d_models=generate_3d_models,
        )
        generate_dev(
            library='CK.lplib',
            author='U. Bruhin',
            version='0.1',
            create_date='2025-04-15T21:39:13Z',
            family=family,
            model=model,
        )

    # C&K PTS645SxxxSMTR92LFS
    family = Family(
        manufacturer='C&K',
        pkg_name_prefix='CK',
        dev_name_prefix='C&K',
        body_size_x=6.0,
        body_size_y=6.0,
        body_size_z=3.45,
        actuator_size=3.5,  # round
        actuator_color='azure4',
        lead_config=GullWingLeadConfig(
            pitch_x=7.95,
            pitch_y=4.5,
            pad_size_x=1.55,
            pad_size_y=1.3,
            thickness=0.3,
            width=0.7,
            span=9.0,
        ),
        datasheet='https://www.ckswitches.com/media/1471/pts645.pdf',
        datasheet_name='PTS645',
        keywords=[],
    )
    models = [
        # 4.3mm
        Model(
            name='PTS645Sx43SMTR92',
            actuator_height=4.3,
            parts=[
                Part(
                    'PTS645SK43SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '260gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SL43SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '130gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SM43SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '160gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SN43SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '100gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SH43SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '200gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SP43SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '320gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SR43SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '360gf', AttributeType.STRING, None),
                    ],
                ),
            ],
            common_part_attributes=[
                Attribute('HEIGHT', '4.3mm', AttributeType.STRING, None),
            ],
        ),
        # 5.0mm
        Model(
            name='PTS645Sx50SMTR92',
            actuator_height=5.0,
            parts=[
                Part(
                    'PTS645SK50SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '260gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SL50SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '130gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SM50SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '160gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SN50SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '100gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SH50SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '200gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SP50SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '320gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SR50SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '360gf', AttributeType.STRING, None),
                    ],
                ),
            ],
            common_part_attributes=[
                Attribute('HEIGHT', '5.0mm', AttributeType.STRING, None),
            ],
        ),
        # 7.0mm
        Model(
            name='PTS645Sx70SMTR92',
            actuator_height=7.0,
            parts=[
                Part(
                    'PTS645SK70SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '260gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SL70SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '130gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SM70SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '160gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SN70SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '100gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SH70SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '200gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SP70SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '320gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SR70SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '360gf', AttributeType.STRING, None),
                    ],
                ),
            ],
            common_part_attributes=[
                Attribute('HEIGHT', '7.0mm', AttributeType.STRING, None),
            ],
        ),
        # 9.5mm
        Model(
            name='PTS645Sx95SMTR92',
            actuator_height=9.5,
            parts=[
                Part(
                    'PTS645SK95SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '260gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SL95SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '130gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SM95SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '160gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SN95SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '100gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SH95SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '200gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SP95SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '320gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SR95SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '360gf', AttributeType.STRING, None),
                    ],
                ),
            ],
            common_part_attributes=[
                Attribute('HEIGHT', '9.5mm', AttributeType.STRING, None),
            ],
        ),
        # 11mm
        Model(
            name='PTS645Sx11SMTR92',
            actuator_height=11.0,
            parts=[
                Part(
                    'PTS645SK11SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '260gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SL11SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '130gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SM11SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '160gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SN11SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '100gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SH11SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '200gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SP11SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '320gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SR11SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '360gf', AttributeType.STRING, None),
                    ],
                ),
            ],
            common_part_attributes=[
                Attribute('HEIGHT', '11mm', AttributeType.STRING, None),
            ],
        ),
        # 13mm
        Model(
            name='PTS645Sx13SMTR92',
            actuator_height=13.0,
            parts=[
                Part(
                    'PTS645SK13SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '260gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SL13SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '130gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SM13SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '160gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SN13SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '100gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SH13SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '200gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SP13SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '320gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SR13SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '360gf', AttributeType.STRING, None),
                    ],
                ),
            ],
            common_part_attributes=[
                Attribute('HEIGHT', '13mm', AttributeType.STRING, None),
            ],
        ),
    ]
    for model in models:
        generate_pkg(
            library='CK.lplib',
            author='U. Bruhin',
            version='0.1',
            create_date='2025-04-15T21:39:13Z',
            family=family,
            model=model,
            generate_3d_models=generate_3d_models,
        )
        generate_dev(
            library='CK.lplib',
            author='U. Bruhin',
            version='0.1',
            create_date='2025-04-15T21:39:13Z',
            family=family,
            model=model,
        )

    # C&K PTS645SJxxxSMTR92LFS
    family = Family(
        manufacturer='C&K',
        pkg_name_prefix='CK',
        dev_name_prefix='C&K',
        body_size_x=6.0,
        body_size_y=6.0,
        body_size_z=3.45,
        actuator_size=(2.4, 2.4),  # rect
        actuator_color='azure4',
        lead_config=GullWingLeadConfig(
            pitch_x=7.95,
            pitch_y=4.5,
            pad_size_x=1.55,
            pad_size_y=1.3,
            thickness=0.3,
            width=0.7,
            span=9.0,
        ),
        datasheet='https://www.ckswitches.com/media/1471/pts645.pdf',
        datasheet_name='PTS645',
        keywords=[],
    )
    models = [
        Model(
            name='PTS645SJx73SMTR92',
            actuator_height=7.3,
            parts=[
                Part(
                    'PTS645SJK43SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '260gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SJL73SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '130gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SJM73SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '160gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SJN73SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '100gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SJH73SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '200gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SJP73SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '320gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SJR73SMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '360gf', AttributeType.STRING, None),
                    ],
                ),
            ],
            common_part_attributes=[
                Attribute('HEIGHT', '7.3mm', AttributeType.STRING, None),
            ],
        ),
    ]
    for model in models:
        generate_pkg(
            library='CK.lplib',
            author='U. Bruhin',
            version='0.1',
            create_date='2025-04-15T21:39:13Z',
            family=family,
            model=model,
            generate_3d_models=generate_3d_models,
        )
        generate_dev(
            library='CK.lplib',
            author='U. Bruhin',
            version='0.1',
            create_date='2025-04-15T21:39:13Z',
            family=family,
            model=model,
        )

    # C&K PTS645SxxxJSMTR92LFS
    family = Family(
        manufacturer='C&K',
        pkg_name_prefix='CK',
        dev_name_prefix='C&K',
        body_size_x=6.0,
        body_size_y=6.0,
        body_size_z=3.45,
        actuator_size=3.5,  # round
        actuator_color='azure4',
        lead_config=JLeadConfig(
            pitch_x=6.0,
            pitch_y=4.5,
            pad_size_x=1.5,
            pad_size_y=1.3,
            thickness=0.3,
            width=0.7,  # Wrong datasheet?
        ),
        datasheet='https://www.ckswitches.com/media/1471/pts645.pdf',
        datasheet_name='PTS645',
        keywords=[],
    )
    models = [
        # 4.3mm
        Model(
            name='PTS645Sx43JSMTR92',
            actuator_height=4.3,
            parts=[
                Part(
                    'PTS645SK43JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '260gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SL43JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '130gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SM43JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '160gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SN43JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '100gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SH43JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '200gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SP43JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '320gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SR43JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '360gf', AttributeType.STRING, None),
                    ],
                ),
            ],
            common_part_attributes=[
                Attribute('HEIGHT', '4.3mm', AttributeType.STRING, None),
            ],
        ),
        # 5.0mm
        Model(
            name='PTS645Sx50JSMTR92',
            actuator_height=5.0,
            parts=[
                Part(
                    'PTS645SK50JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '260gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SL50JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '130gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SM50JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '160gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SN50JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '100gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SH50JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '200gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SP50JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '320gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SR50JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '360gf', AttributeType.STRING, None),
                    ],
                ),
            ],
            common_part_attributes=[
                Attribute('HEIGHT', '5.0mm', AttributeType.STRING, None),
            ],
        ),
        # 7.0mm
        Model(
            name='PTS645Sx70JSMTR92',
            actuator_height=7.0,
            parts=[
                Part(
                    'PTS645SK70JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '260gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SL70JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '130gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SM70JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '160gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SN70JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '100gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SH70JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '200gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SP70JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '320gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SR70JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '360gf', AttributeType.STRING, None),
                    ],
                ),
            ],
            common_part_attributes=[
                Attribute('HEIGHT', '7.0mm', AttributeType.STRING, None),
            ],
        ),
        # 9.5mm
        Model(
            name='PTS645Sx95JSMTR92',
            actuator_height=9.5,
            parts=[
                Part(
                    'PTS645SK95JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '260gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SL95JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '130gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SM95JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '160gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SN95JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '100gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SH95JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '200gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SP95JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '320gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SR95JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '360gf', AttributeType.STRING, None),
                    ],
                ),
            ],
            common_part_attributes=[
                Attribute('HEIGHT', '9.5mm', AttributeType.STRING, None),
            ],
        ),
        # 11mm
        Model(
            name='PTS645Sx11JSMTR92',
            actuator_height=11.0,
            parts=[
                Part(
                    'PTS645SK11JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '260gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SL11JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '130gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SM11JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '160gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SN11JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '100gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SH11JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '200gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SP11JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '320gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SR11JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '360gf', AttributeType.STRING, None),
                    ],
                ),
            ],
            common_part_attributes=[
                Attribute('HEIGHT', '11mm', AttributeType.STRING, None),
            ],
        ),
        # 13mm
        Model(
            name='PTS645Sx13JSMTR92',
            actuator_height=13.0,
            parts=[
                Part(
                    'PTS645SK13JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '260gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SL13JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '130gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SM13JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '160gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SN13JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '100gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SH13JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '200gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SP13JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '320gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SR13JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '360gf', AttributeType.STRING, None),
                    ],
                ),
            ],
            common_part_attributes=[
                Attribute('HEIGHT', '13mm', AttributeType.STRING, None),
            ],
        ),
    ]
    for model in models:
        generate_pkg(
            library='CK.lplib',
            author='U. Bruhin',
            version='0.1',
            create_date='2025-04-15T21:39:13Z',
            family=family,
            model=model,
            generate_3d_models=generate_3d_models,
        )
        generate_dev(
            library='CK.lplib',
            author='U. Bruhin',
            version='0.1',
            create_date='2025-04-15T21:39:13Z',
            family=family,
            model=model,
        )

    # C&K PTS645SJxxxJSMTR92LFS
    family = Family(
        manufacturer='C&K',
        pkg_name_prefix='CK',
        dev_name_prefix='C&K',
        body_size_x=6.0,
        body_size_y=6.0,
        body_size_z=3.45,
        actuator_size=(2.4, 2.4),  # rect
        actuator_color='azure4',
        lead_config=JLeadConfig(
            pitch_x=6.0,
            pitch_y=4.5,
            pad_size_x=1.5,
            pad_size_y=1.3,
            thickness=0.3,
            width=0.7,  # Wrong datasheet?
        ),
        datasheet='https://www.ckswitches.com/media/1471/pts645.pdf',
        datasheet_name='PTS645',
        keywords=[],
    )
    models = [
        Model(
            name='PTS645SJx73JSMTR92',
            actuator_height=7.3,
            parts=[
                Part(
                    'PTS645SJK43JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '260gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SJL73JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '130gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SJM73JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '160gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SJN73JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '100gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SJH73JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '200gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SJP73JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '320gf', AttributeType.STRING, None),
                    ],
                ),
                Part(
                    'PTS645SJR73JSMTR92LFS',
                    Manufacturer('C&K'),
                    [
                        Attribute('FORCE', '360gf', AttributeType.STRING, None),
                    ],
                ),
            ],
            common_part_attributes=[
                Attribute('HEIGHT', '7.3mm', AttributeType.STRING, None),
            ],
        ),
    ]
    for model in models:
        generate_pkg(
            library='CK.lplib',
            author='U. Bruhin',
            version='0.1',
            create_date='2025-04-15T21:39:13Z',
            family=family,
            model=model,
            generate_3d_models=generate_3d_models,
        )
        generate_dev(
            library='CK.lplib',
            author='U. Bruhin',
            version='0.1',
            create_date='2025-04-15T21:39:13Z',
            family=family,
            model=model,
        )

    save_cache(uuid_cache_file, uuid_cache)
