"""
Generate DIP switches
"""

from os import path
from uuid import uuid4

from typing import Optional

from common import init_cache, now, save_cache
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
    Rotation,
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


if __name__ == '__main__':
    # Symbols & Components
    for i in [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14]:
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

    save_cache(uuid_cache_file, uuid_cache)
