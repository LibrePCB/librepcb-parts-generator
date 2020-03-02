"""
Generate STM32 microcontroller symbols, components and devices.

Data source: https://github.com/LibrePCB/stm32-pinout

In order to reduce the number of symbols, the following items are reused:

- For every family, MCUs with the same number of pins per pin class are merged
  into a single symbol
- Components are merged if they share the same pinout.

Example:

+--------------------------------------+------------------+---------------+
| Symbol                               | Component        | Device        |
+--------------------------------------+------------------+---------------+
| STM32L0 Boot-1 IO-23 Power-7         | STM32L071KBUx    | STM32L071KBUx |
|--------------------------------------|------------------|---------------|
| STM32L0 Boot-1 IO-25 Power-5 Reset-1 | STM32L071K[BZ]Tx | STM32L071KBTx |
|                                      |                  |---------------|
|                                      |                  | STM32L071KZTx |
+--------------------------------------+------------------+---------------+

"""
import argparse
import hashlib
import json
import math
import re
from collections import defaultdict
from os import listdir, makedirs, path
from uuid import uuid4

from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import common
from common import init_cache, save_cache
from entities.common import (
    Align, Angle, Author, Category, Created, Deprecated, Description, Fill, GrabArea, Height, Keywords, Layer, Length,
    Name, Polygon, Position, Rotation, Text, Value, Version, Vertex, Width
)
from entities.component import (
    Clock, Component, DefaultValue, ForcedNet, Gate, Negated, Norm, PinSignalMap, Prefix, Required, Role, SchematicOnly,
    Signal, SignalUUID, Suffix, SymbolUUID, TextDesignator, Variant
)
from entities.device import ComponentPad, ComponentUUID, Device, PackageUUID
from entities.symbol import Pin as SymbolPin
from entities.symbol import Symbol

grid = 2.54  # Grid size in mm
width = 10  # Symbol width in grid units
line_width = 0.25  # Line width in mm
text_height = 2.5  # Name / value text height
generator = 'librepcb-parts-generator (generate_stm32.py)'
keywords = Keywords('stm32, stm, st, mcu, microcontroller, arm, cortex')
author = Author('Danilo Bargen, John Eaton')
cmpcat = Category('22151601-c2d9-419a-87bc-266f9c7c3459')

# Initialize UUID cache
uuid_cache_file = 'uuid_cache_stm32.csv'
uuid_cache = init_cache(uuid_cache_file)


def uuid(category: str, full_name: str, identifier: str) -> str:
    """
    Return a uuid for the specified item.

    Params:
        category:
            For example 'cmp' or 'sym'.
        full_name:
            For example "STM32WB55CEUx".
        identifier:
            For example 'sym' or 'pin-pb9'.
    """
    key = '{}-{}-{}'.format(category, full_name, identifier).lower().replace(' ', '~')
    if key not in uuid_cache:
        uuid_cache[key] = str(uuid4())
    return uuid_cache[key]


class Pin:
    """
    Data class for a MCU pin.
    """
    def __init__(
        self,
        number: str,
        name: str,
        pin_type: str,
    ):
        self.number = number
        self.name = name
        self.pin_type = pin_type


class SymbolPinPlacement:
    def __init__(self) -> None:
        self.left = []  # type: List[Tuple[str, int]]
        self.right = []  # type: List[Tuple[str, int]]

    def add_left_pin(self, pin_name: str, y_pos: int) -> None:
        self.left.append((pin_name, y_pos))

    def add_right_pin(self, pin_name: str, y_pos: int) -> None:
        self.right.append((pin_name, y_pos))

    def sort(self) -> None:
        """
        Sort pins in-place by y-position (top first).
        """
        self.left.sort(key=lambda x: -x[1])
        self.right.sort(key=lambda x: -x[1])

    def pins(self, width: int, grid: float) -> List[Tuple[str, Position, Rotation]]:
        """
        Return all pins spaced with the specified grid size.
        """
        dx = (width + 2) * grid / 2
        return [(l[0], Position(-dx, l[1] * grid), Rotation(0.0)) for l in self.left] + \
            [(r[0], Position(dx, r[1] * grid), Rotation(180.0)) for r in self.right]

    def maxmin_y(self, grid: float) -> Tuple[float, float]:
        """
        Return max and min y coordinates.
        """
        return (
            (max(self.left[0][1], self.right[0][1]) + 1) * grid,
            (min(self.left[-1][1], self.right[-1][1]) - 1) * grid,
        )


class PinName:
    """
    This class holds a generic pin name (like IO7) and a concrete pin name (like PB3).
    """
    def __init__(self, generic: str, concrete: str):
        self.generic = generic
        self.concrete = concrete

    def __str__(self) -> str:
        return '{}/{}'.format(self.generic, self.concrete)


class MCU:
    """
    Data class for a MCU.
    """
    def __init__(self, ref: str, info: Dict[str, Any], pins: Iterable[Pin]):
        # Note: Don't use this directly, use `from_json` instead
        self.ref = ref
        self.name = info['names']['name']
        self.family = info['names']['family']
        self.package = info['package']
        self.pins = list(pins)
        self.flash = '{} KiB'.format(info['info']['flash'])
        self.ram = '{} KiB'.format(info['info']['ram'])
        self.io_count = info['info']['io']  # type: int
        if 'frequency' in info['info']:
            self.frequency = '{} MHz'.format(info['info']['frequency'])  # type: Optional[str]
        else:
            self.frequency = None
        if 'voltage' in info['info']:
            self.voltage = '{:.2}-{:.2}V'.format(
                info['info']['voltage']['min'],
                info['info']['voltage']['max'],
            )  # type: Optional[str]
        else:
            self.voltage = None
        if 'temperature' in info['info']:
            self.temperature = '{:.0f}-{:.0f}°C'.format(
                info['info']['temperature']['min'],
                info['info']['temperature']['max'],
            )  # type: Optional[str]
        else:
            self.temperature = None

    @staticmethod
    def _cleanup_type(pin_type: str) -> str:
        return pin_type.replace('/', '')

    @staticmethod
    def _cleanup_pin_name(pin_name: str) -> str:
        # WARNING: Changing this has an effect on the pinout hash!
        if 'OSC' in pin_name:
            # Oscillator pins sometimes have variations between different MCUs, even though
            # the rest of the pinout is identical. Therefore, normalize those pin names.
            val = pin_name
            val = re.sub(r'\s*-\s*OSC', r'-OSC', val)
            val = re.sub(r'\s*/\s*OSC', r'-OSC', val)
            val = re.sub(r'([0-9])OSC', r'\1-OSC', val)
            return val
        return pin_name

    @classmethod
    def from_json(cls, ref: str, info: Dict[str, Any]) -> 'MCU':
        pins = []
        for entry in info['pinout']:
            pin = Pin(
                number=entry['position'],
                name=cls._cleanup_pin_name(entry['name']),
                pin_type=cls._cleanup_type(entry['type']),
            )
            pins.append(pin)
        return MCU(ref, info, pins)

    def pin_types(self) -> Set[str]:
        """
        Return a set containing all pin types present in this MCU.
        """
        return {p.pin_type for p in self.pins}

    def get_pins_by_type(self, pin_type: str) -> List[Pin]:
        """
        Return all pins of that type, sorted.
        """
        pins = [p for p in self.pins if p.pin_type == pin_type]
        pins.sort(key=lambda p: (p.name, p.number))
        return pins

    def get_pin_names_by_type(self, pin_type: str) -> List[PinName]:
        """
        Return all pin names of that type (without duplicates), sorted.
        """
        pins = self.get_pins_by_type(pin_type)
        known_names = set()  # type: Set[str]
        result = []
        i = 1
        for pin in pins:
            if pin.name in known_names:
                continue
            result.append(PinName(
                '{}{}'.format(pin_type, i),
                pin.name,
            ))
            known_names.add(pin.name)
            i += 1
        return result

    @property
    def ref_without_flash(self) -> str:
        """
        Return the ref with the flash size replaced with an 'x'.

        Example:

        - STM32F429NEHx -> STM32F429NxHx
        - STM32L552CETxP -> STM32L552CxTxP

        """
        return self.ref[:10] + 'x' + self.ref[11:]

    def ref_for_flash_variants(self, variants: List[str]) -> str:
        """
        Return the name that integrates all flash size variants.

        Args:
            variants:
                List of refs. Must share the same "ref without flash".

        Example:

        - STM32F429IEHx + STM32F429IGHx + STM32F429IIHx = STM32F429I[EGI]Hx.

        """
        for variant in variants:
            assert variant[:10] == self.ref[:10]
            assert variant[11:] == self.ref[11:]
        flash_variants = sorted([ref[10] for ref in variants])
        if len(flash_variants) > 1:
            return '{}[{}]{}'.format(self.ref[:10], ''.join(flash_variants), self.ref[11:])
        else:
            return self.ref

    @property
    def symbol_name(self) -> str:
        """
        Get a symbol name based on pin types.
        """
        name_parts = [self.family]
        for pin_type in sorted(self.pin_types()):
            count = len(self.get_pin_names_by_type(pin_type))
            name_parts.append('{}-{}'.format(pin_type, count))
        return ' '.join(name_parts)

    @property
    def symbol_identifier(self) -> str:
        """
        Get the symbol identifier, used as a key for the UUID lookup.
        """
        return self.symbol_name \
            .lower() \
            .replace(' ', '_') \
            .replace('-', '~') \
            .replace('/', '')

    @property
    def symbol_description(self) -> str:
        """
        Get a description of the symbol.
        """
        description = 'A {} MCU by ST Microelectronics with the following pins:\\n\\n'.format(self.family)
        for pin_type in sorted(self.pin_types()):
            count = len(self.get_pin_names_by_type(pin_type))
            description += '- {} {} pins\\n'.format(count, pin_type)
        description += '\\nGenerated with {}'.format(generator)
        return description

    @property
    def component_identifier(self) -> str:
        """
        Return the component identifier, composed of the ref without flash and
        the pinout hash.
        """
        return '{}~{}'.format(self.ref_without_flash, self.pinout_hash).lower()

    @property
    def component_description(self) -> str:
        """
        Get a description of the component.
        """
        description = 'A {} MCU by ST Microelectronics.\\n\\n'.format(self.ref_without_flash)
        description += 'Package: {}\\nI/Os: {}\\nFrequency: {}\\n'.format(
            self.package, self.io_count, self.frequency,
        )
        description += '\\nGenerated with {}'.format(generator)
        return description

    @property
    def description(self) -> str:
        description = 'A {} MCU by ST Microelectronics.\\n\\n'.format(self.name)
        description += 'Package: {}\\nFlash: {}\\nRAM: {}\\nI/Os: {}\\nFrequency: {}\\n'.format(
            self.package, self.flash, self.ram, self.io_count, self.frequency,
        )
        if self.voltage:
            description += 'Voltage: {}\\n'.format(self.voltage)
        if self.temperature:
            description += 'Temperature range: {}\\n'.format(self.temperature)
        description += '\\nGenerated with {}'.format(generator)
        return description

    @property
    def pinout_hash(self) -> str:
        """
        Return a hash of the pinout.

        Before hashing, the pins are sorted *alphanumerically* by pin type
        followed by pin name (io_pa15 comes before io_pa2).

        """
        pinout = ','.join(sorted('{}_{}'.format(pin.pin_type, pin.name) for pin in self.pins)).lower()
        return hashlib.sha1(pinout.encode('ascii')).hexdigest()

    def generate_placement_data(self, debug: bool = False) -> Tuple[SymbolPinPlacement, Dict[str, str]]:
        """
        This method will generate placement data for the symbol.

        It will split up the pins into two lists, the left side and the right
        side of the symbol. Every pin will have a corresponding y-coordinate
        (an integer which needs to be multiplied with the desired grid size).

        General approach:

        +--------------+
        | Reset    I/O |
        |              |
        | Power        |
        |              |
        | MonoIO       |
        |              |
        | Boot         |
        |              |
        | NC           |
        +--------------+

        Returned data: A tuple with the abstract pin placement info, as well as
        a mapping from abstract name to real name.

        """
        # Ensure that only known pin types are present
        unknown_pin_types = self.pin_types() - {'Reset', 'Power', 'MonoIO', 'Boot', 'NC', 'IO'}
        assert len(unknown_pin_types) == 0, 'Unknown pin types: {}'.format(unknown_pin_types)

        # Determine number of pins on both sides
        left_pins = [self.get_pin_names_by_type(t) for t in ['Reset', 'Power', 'MonoIO', 'Boot', 'NC']]
        left_pins = [group for group in left_pins if len(group) > 0]
        left_count = sum(len(group) for group in left_pins)
        right_pins = [self.get_pin_names_by_type(t) for t in ['IO']]
        right_pins = [group for group in right_pins if len(group) > 0]
        right_count = sum(len(group) for group in right_pins)
        height = max([left_count + len(left_pins) - 1, right_count + len(right_pins) - 1])
        max_y = math.ceil(height / 2)
        if debug:
            print('Placement info:')
            print('  Left {} pins {} steps'.format(
                left_count,
                left_count + len(left_pins) - 1,
            ))
            print('  Right {} pins {} steps'.format(
                right_count,
                right_count + len(right_pins) - 1,
            ))
            print('  Height: {} steps, max_y: {} steps'.format(height, max_y))

        # Generate placement info
        y = max_y
        placement = SymbolPinPlacement()
        for i, group in enumerate(left_pins):
            if i > 0:
                # Put a space between groups
                y -= 1
            for pin_name in group:
                placement.add_left_pin(pin_name.generic, y)
                y -= 1
        y = max_y
        for i, group in enumerate(right_pins):
            if i > 0:
                # Put a space between groups
                y -= 1
            for pin_name in group:
                placement.add_right_pin(pin_name.generic, y)
                y -= 1
        placement.sort()

        # Dict that holds mapping from generic name to concrete name
        name_mapping = {}
        for group in left_pins + right_pins:
            for pin_name in group:
                name_mapping[pin_name.generic] = pin_name.concrete

        if debug:
            print('Placement:')
            print('  Left:')
            for (pin_name_str, y) in placement.left:
                print('    {} {}'.format(y, pin_name_str))
            print('  Right:')
            for (pin_name_str, y) in placement.right:
                print('    {} {}'.format(y, pin_name_str))

        return (placement, name_mapping)

    def __repr__(self) -> str:
        return '<MCU {} ({} pins, {})>'.format(self.ref, len(self.pins), self.package)


def _make(dirpath: str) -> None:
    if not (path.exists(dirpath) and path.isdir(dirpath)):
        makedirs(dirpath)


def generate_sym(mcu: MCU, symbol_map: Dict[str, str], debug: bool = False) -> None:
    assert mcu.symbol_identifier not in symbol_map

    sym_version = '0.1'

    (placement, pin_mapping) = mcu.generate_placement_data(debug)
    if debug:
        print(pin_mapping)

    uuid_sym = uuid('sym', mcu.symbol_identifier, 'sym')
    symbol = Symbol(
        uuid_sym,
        Name(mcu.symbol_name),
        Description(mcu.symbol_description),
        keywords,
        author,
        Version(sym_version),
        Created('2020-01-30T20:55:23Z'),
        cmpcat,
    )
    placement_pins = placement.pins(width, grid)
    placement_pins.sort(key=lambda x: (x[1].x, x[1].y))
    for pin_name, position, rotation in placement.pins(width, grid):
        symbol.add_pin(SymbolPin(
            uuid('sym', mcu.symbol_identifier, 'pin-{}'.format(pin_name)),
            Name(pin_name),
            position,
            rotation,
            Length(grid),
        ))
    polygon = Polygon(
        uuid('sym', mcu.symbol_identifier, 'polygon'),
        Layer('sym_outlines'),
        Width(line_width),
        Fill(False),
        GrabArea(True),
    )
    (max_y, min_y) = placement.maxmin_y(grid)
    dx = width * grid / 2
    polygon.add_vertex(Vertex(Position(-dx, max_y), Angle(0.0)))
    polygon.add_vertex(Vertex(Position( dx, max_y), Angle(0.0)))
    polygon.add_vertex(Vertex(Position( dx, min_y), Angle(0.0)))
    polygon.add_vertex(Vertex(Position(-dx, min_y), Angle(0.0)))
    polygon.add_vertex(Vertex(Position(-dx, max_y), Angle(0.0)))
    symbol.add_polygon(polygon)

    text_name = Text(
        uuid('sym', mcu.symbol_identifier, 'text-name'),
        Layer('sym_names'),
        Value('{{NAME}}'),
        Align('left bottom'),
        Height(text_height),
        Position(-dx, max_y),
        Rotation(0.0),
    )
    text_value = Text(
        uuid('sym', mcu.symbol_identifier, 'text-value'),
        Layer('sym_values'),
        Value('{{VALUE}}'),
        Align('left top'),
        Height(text_height),
        Position(-dx, min_y),
        Rotation(0.0),
    )
    symbol.add_text(text_name)
    symbol.add_text(text_value)

    dirpath = 'out/stm32/sym'
    sym_dir_path = path.join(dirpath, uuid_sym)
    if not (path.exists(sym_dir_path) and path.isdir(sym_dir_path)):
        makedirs(sym_dir_path)
    with open(path.join(sym_dir_path, '.librepcb-sym'), 'w') as f:
        f.write('0.1\n')
    with open(path.join(sym_dir_path, 'symbol.lp'), 'w') as f:
        f.write(str(symbol))
        f.write('\n')

    symbol_map[mcu.symbol_identifier] = uuid_sym

    print('Wrote sym {}'.format(mcu.symbol_name))


def generate_cmp(name: str, mcu: MCU, symbol_map: Dict[str, str], debug: bool = False) -> None:
    """
    When generating components, to reduce the number of components, they are
    merged as follows:

    - For every MCU, the "ref without flash" is calculated by replacing the
      11th character in the ref name with an `x` and cutting off everything after
      the package character.
    - MCUs that share the same pinout will be merged if their ref names without
      flash are the same
    - The name of the component will be generated as follows: STM32F429IEHx +
      STM32F429IGHx + STM32F429IIHx = STM32F429I[EGI]Hx.
    - To achieve a stable UUID even if new MCUs are added, the "ref without
      flash" is combined with the SHA1 hash of the pins.

    Because renaming the pinout might result in a different UUID, when
    upgrading the stm32-pinout database, changes (but not additions) must be
    analyzed manually.

    """
    (placement, pin_mapping) = mcu.generate_placement_data(debug)

    cmp_version = '0.1'

    component = Component(
        uuid('cmp', mcu.component_identifier, 'cmp'),
        Name(name),
        Description(mcu.component_description),
        keywords,
        author,
        Version(cmp_version),
        Created('2020-01-30T20:55:23Z'),
        Deprecated(False),
        cmpcat,
        SchematicOnly(False),
        DefaultValue('{{PARTNUMBER or DEVICE or COMPONENT}}'),
        Prefix('U'),
    )

    # Add signals
    signals = {pin.name for pin in mcu.pins}
    for signal in signals:
        component.add_signal(Signal(
            uuid('cmp', mcu.component_identifier, 'signal-{}'.format(signal)),
            Name(signal),
            Role.PASSIVE,
            Required(False),
            Negated(False),
            Clock(False),
            ForcedNet(''),
        ))

    # Add symbol variant
    gate = Gate(
        uuid('cmp', mcu.component_identifier, 'variant-single-gate1'),
        SymbolUUID(uuid('sym', mcu.symbol_identifier, 'sym')),
        Position(0, 0),
        Rotation(0.0),
        Required(True),
        Suffix(''),
    )
    for generic, concrete in pin_mapping.items():
        gate.add_pin_signal_map(PinSignalMap(
            uuid('sym', mcu.symbol_identifier, 'pin-{}'.format(generic)),
            SignalUUID(uuid('cmp', mcu.component_identifier, 'signal-{}'.format(concrete))),
            TextDesignator.SIGNAL_NAME,
        ))
    component.add_variant(Variant(
        uuid('cmp', mcu.component_identifier, 'variant-single'),
        Norm.EMPTY,
        Name('single'),
        Description('Symbol with all MCU pins'),
        gate,
    ))

    component.serialize('out/stm32/cmp')

    print('Wrote cmp {}'.format(name))


def generate_dev(mcu: MCU, symbol_map: Dict[str, str], base_lib_path: str, debug: bool = False) -> None:
    """
    A device will be generated for every MCU ref.
    """
    (placement, pin_mapping) = mcu.generate_placement_data(debug)

    name = mcu.ref
    dev_version = '0.1'

    package_uuid_mapping = {
        'LQFP32':  'd1944164-969d-421f-8b46-1e79fc368195',  # LQFP80P900X900X140-32
        'LQFP48':  '584b7c26-5a8e-4a2b-807a-977edd1df991',  # LQFP50P900X900X140-48
        'LQFP100': 'f74cdcb2-833d-4877-876f-56d4c15b5cb8',  # LQFP50P1600X1600X140-100
        'LQFP144': '2fc34b46-a86d-40e3-9dd1-def143ac3318',  # LQFP50P2200X2200X140-144
        'LQFP176': '43ab9eca-7912-433f-afaa-61d3ec6c84b2',  # LQFP50P2600X2600X140-176
    }
    if mcu.package not in package_uuid_mapping:
        print('Skipping dev {} (missing package {})'.format(name, mcu.package))
        return

    pad_uuid_mapping = common.get_pad_uuids(base_lib_path, package_uuid_mapping[mcu.package])

    device = Device(
        uuid('dev', mcu.ref, 'dev'),
        Name(mcu.ref),
        Description(mcu.description),
        keywords,
        author,
        Version(dev_version),
        Created('2020-03-01T01:55:20Z'),
        Deprecated(False),
        cmpcat,
        ComponentUUID(uuid('cmp', mcu.component_identifier, 'cmp')),
        PackageUUID(package_uuid_mapping[mcu.package]),
    )
    for pin in mcu.pins:
        pad_uuid = pad_uuid_mapping[pin.number]
        device.add_pad(ComponentPad(
            pad_uuid,
            SignalUUID(uuid('cmp', mcu.component_identifier, 'signal-{}'.format(pin.name))),
        ))

    device.serialize('out/stm32/dev')

    print('Wrote dev {}'.format(name))


def generate(data: Dict[str, MCU], base_lib_path: str, debug: bool = False) -> None:
    _make('out')
    _make('out/stm32')
    _make('out/stm32/sym')
    _make('out/stm32/cmp')

    # A map mapping symbol names to UUIDs
    symbol_map = {}  # type: Dict[str, str]

    print('\nProcessing {} MCUs'.format(len(data)))

    # Group symbols
    symbols = defaultdict(list)  # type: Dict[str, List[MCU]]
    for mcu in data.values():
        symbols[mcu.symbol_identifier].append(mcu)
    print('Generating {} symbols'.format(len(symbols)))

    # Group components
    components_tmp = defaultdict(list)  # type: Dict[str, List[MCU]]
    for mcu in data.values():
        components_tmp[mcu.component_identifier].append(mcu)
    components = defaultdict(list)  # type: Dict[str, List[MCU]]
    for k, v in components_tmp.items():
        combined_name = v[0].ref_for_flash_variants([mcu.ref for mcu in v])
        components[combined_name] = v
    print('Generating {} components'.format(len(components)))

    # No grouping for devices
    print('Generating {} devices'.format(len(data)))

    # Generate
    print()
    for mcus in symbols.values():
        generate_sym(mcus[0], symbol_map, debug)
    for name, mcus in components.items():
        generate_cmp(name, mcus[0], symbol_map, debug)
    for mcu in data.values():
        generate_dev(mcu, symbol_map, base_lib_path, debug)

    # Check for duplicates
    print()
    d = defaultdict(int)  # type: Dict[str, int]
    for mcus in components.values():
        d[mcus[0].ref_without_flash] += 1
    # Sometimes parts have the same pin names, but different writings (e.g.
    # `PC14 / OSC32_IN` vs `PC14-OSC32_IN`). These differences should be
    # filtered out by the cleanup function.
    #
    # Whitelist contains parts that actually have different variants, verified
    # manually by comparing pinout files.
    #
    # To compare more easily:
    # for f in data/STM32F302V*T*.json; do cat $f | jq -c '.pinout[] | del(.signals)' > cmp/$(basename $f); done
    whitelist = [
        'STM32F302VxTx', 'STM32F303RxTx', 'STM32F303VxYx', 'STM32F302RxTx', 'STM32L151QxHx',
        'STM32L152QxHx', 'STM32L010KxTx', 'STM32F030CxTx', 'STM32F303VxTx', 'STM32F030RxTx',
        'STM32L010RxTx',
    ]
    for kk, vv in d.items():
        if vv > 1 and kk not in whitelist:
            print('WARNING: MCU {} has {} pinout variants'.format(kk, vv))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate STM32 library elements')
    parser.add_argument(
        '--data-dir', metavar='path-to-data-dir', required=True,
        help='path to the data dir from https://github.com/LibrePCB/stm32-pinout',
    )
    parser.add_argument(
        '--base-lib', metavar='path-to-base-lib', required=True,
        help='path to the LibrePCB-Base.lplib library',
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='print debug information',
    )
    args = parser.parse_args()

    # Load and parse all data
    data = {}  # type: Dict[str, MCU]
    for filename in listdir(args.data_dir):
        match = re.match(r'(STM32.*)\.json$', filename)
        if match:
            mcu_ref = match.group(1)
            info_path = path.join(args.data_dir, '{}.json'.format(mcu_ref))
            with open(info_path, 'r') as f:
                info = json.loads(f.read())
                mcu = MCU.from_json(mcu_ref, info)
                assert None not in mcu.pin_types()
            assert mcu_ref not in data
            data[mcu_ref] = mcu

    # Generate library elements
    generate(data, args.base_lib, args.debug)

    print()
    save_cache(uuid_cache_file, uuid_cache)
