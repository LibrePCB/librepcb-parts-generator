from os import makedirs, path

from typing import List

from .common import (
    Author, BoolValue, Category, Created, Deprecated, Description, EnumValue, Keywords, Name, Position, Rotation,
    StringValue, UUIDValue, Version
)
from .helper import indent_entities


class DefaultValue(StringValue):
    def __init__(self, default_value: str):
        super().__init__('default_value', default_value)


class Prefix(StringValue):
    def __init__(self, prefix: str):
        super().__init__('prefix', prefix)


class SchematicOnly(BoolValue):
    def __init__(self, schematic_only: bool):
        super().__init__('schematic_only', schematic_only)


class Role(EnumValue):
    PASSIVE = 'passive'

    def get_name(self) -> str:
        return 'role'


class Required(BoolValue):
    def __init__(self, required: bool):
        super().__init__('required', required)


class Negated(BoolValue):
    def __init__(self, negated: bool):
        super().__init__('negated', negated)


class Clock(BoolValue):
    def __init__(self, clock: bool):
        super().__init__('clock', clock)


class ForcedNet(StringValue):
    def __init__(self, forced_net: str):
        super().__init__('forced_net', forced_net)


class Signal():
    def __init__(self, uuid: str, name: Name, role: Role, required: Required,
                 negated: Negated, clock: Clock, forced_net: ForcedNet):
        self.uuid = uuid
        self.name = name
        self.role = role
        self.required = required
        self.negated = negated
        self.clock = clock
        self.forced_net = forced_net

    def __str__(self) -> str:
        ret = '(signal {} {} {}\n'.format(self.uuid, self.name, self.role) +\
            ' {} {} {} {}\n'.format(self.required, self.negated, self.clock, self.forced_net) +\
            ')'
        return ret


class SymbolUUID(UUIDValue):
    def __init__(self, symbol_uuid: str):
        super().__init__('symbol', symbol_uuid)


class SignalUUID(UUIDValue):
    def __init__(self, signal_uuid: str):
        super().__init__('signal', signal_uuid)


class TextDesignator(EnumValue):
    SYMBOL_PIN_NAME = 'pin'
    SIGNAL_NAME = 'signal'

    def get_name(self) -> str:
        return 'text'


class PinSignalMap():
    def __init__(self, pin_uuid: str, signal_uuid: SignalUUID,
                 text_designator: TextDesignator):
        self.pin_uuid = pin_uuid
        self.signal_uuid = signal_uuid
        self.text_designator = text_designator

    def __str__(self) -> str:
        return '(pin {} {} {})'.format(self.pin_uuid, self.signal_uuid, self.text_designator)


class Suffix(StringValue):
    def __init__(self, suffix: str):
        super().__init__('suffix', suffix)


class Gate():
    def __init__(self, uuid: str, symbol_uuid: SymbolUUID, position: Position,
                 rotation: Rotation, required: Required, suffix: Suffix):
        self.uuid = uuid
        self.symbol_uuid = symbol_uuid
        self.position = position
        self.rotation = rotation
        self.required = required
        self.suffix = suffix
        self.pins = []  # type: List[PinSignalMap]

    def add_pin_signal_map(self, pin_signal_map: PinSignalMap) -> None:
        self.pins.append(pin_signal_map)

    def __str__(self) -> str:
        ret = '(gate {}\n'.format(self.uuid) +\
            ' {}\n'.format(self.symbol_uuid) +\
            ' {} {} {} {}\n'.format(self.position, self.rotation, self.required, self.suffix)
        pin_lines = []
        for pin in self.pins:
            pin_lines.append(' {}'.format(pin))
        ret += '\n'.join(sorted(pin_lines))
        ret += '\n)'
        return ret


class Norm(EnumValue):
    EMPTY = '""'
    IEEE_315 = '"IEEE 315"'
    IEC_60617 = '"IEC 60617"'

    def get_name(self) -> str:
        return 'norm'


class Variant:
    def __init__(self, uuid: str, norm: Norm, name: Name, description: Description):
        self.uuid = uuid
        self.norm = norm
        self.name = name
        self.description = description
        self.gates = []  # type: List[Gate]

    def add_gate(self, gate_map: Gate) -> None:
        self.gates.append(gate_map)

    def __str__(self) -> str:
        ret = '(variant {} {}\n'.format(self.uuid, self.norm) +\
            ' {}\n'.format(self.name) +\
            ' {}\n'.format(self.description)
        gate_lines = []
        for gate in self.gates:
            gate_lines.append(' {}'.format(gate))
        ret += '\n'.join(sorted(gate_lines))
        ret += '\n)'
        return ret


class Component:
    def __init__(self, uuid: str, name: Name, description: Description,
                 keywords: Keywords, author: Author, version: Version,
                 created: Created, deprecated: Deprecated, category: Category,
                 schematic_only: SchematicOnly,
                 default_value: DefaultValue, prefix: Prefix):
        self.uuid = uuid
        self.name = name
        self.description = description
        self.keywords = keywords
        self.author = author
        self.version = version
        self.created = created
        self.deprecated = deprecated
        self.category = category
        self.schematic_only = schematic_only
        self.default_value = default_value
        self.prefix = prefix
        self.signals = []  # type: List[Signal]
        self.variants = []  # type: List[Variant]

    def __str__(self) -> str:
        ret = '(librepcb_component {}\n'.format(self.uuid) +\
            ' {}\n'.format(self.name) +\
            ' {}\n'.format(self.description) +\
            ' {}\n'.format(self.keywords) +\
            ' {}\n'.format(self.author) +\
            ' {}\n'.format(self.version) +\
            ' {}\n'.format(self.created) +\
            ' {}\n'.format(self.deprecated) +\
            ' {}\n'.format(self.category) +\
            ' {}\n'.format(self.schematic_only) +\
            ' {}\n'.format(self.default_value) +\
            ' {}\n'.format(self.prefix)
        ret += indent_entities(self.signals)
        ret += indent_entities(self.variants)
        ret += ')'
        return ret

    def add_signal(self, signal: Signal) -> None:
        self.signals.append(signal)

    def add_variant(self, variant: Variant) -> None:
        self.variants.append(variant)

    def serialize(self, output_directory: str) -> None:
        cmp_dir_path = path.join(output_directory, self.uuid)
        if not (path.exists(cmp_dir_path) and path.isdir(cmp_dir_path)):
            makedirs(cmp_dir_path)
        with open(path.join(cmp_dir_path, '.librepcb-cmp'), 'w') as f:
            f.write('0.1\n')
        with open(path.join(cmp_dir_path, 'component.lp'), 'w') as f:
            f.write(str(self))
            f.write('\n')
