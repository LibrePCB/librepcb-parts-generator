"""
Generate STM32 microcontroller symbols, components and devices.

Data source: https://github.com/LibrePCB/stm32-pinout

"""
import argparse
from collections import OrderedDict
import csv
import json
import math
from os import listdir, makedirs, path
import re
from uuid import uuid4

from typing import Iterable, List, Set, Tuple

from common import init_cache, save_cache
from entities.common import (
    Align, Angle, Author, Category, Created, Description, Fill, GrabArea, Height, Keywords, Layer, Length, Name,
    Polygon, Position, Rotation, Text, Value, Version, Vertex, Width
)
from entities.symbol import Pin as SymbolPin
from entities.symbol import Symbol

grid = 2.54  # Grid size in mm
width = 10  # Symbol width in grid units
line_width = 0.25  # Line width in mm
text_height = 2.5  # Name / value text height
generator = 'librepcb-parts-generator (generate_stm32.py)'

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
        position: str,
        name: str,
        pin_type: str,
    ):
        self.position = position
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


class MCU:
    """
    Data class for a MCU.
    """
    def __init__(self, ref: str, info: dict, pins: Iterable[Pin]):
        self.ref = ref
        self.name = info['part_no']
        self.package = info['package']
        self.pins = list(pins)
        self.boards = info['boards']
        self.flash = info['flash']
        self.ram = info['ram']
        self.io = info['io']
        self.frequency = info['frequency']

    @staticmethod
    def from_dictreader(ref: str, info: dict, reader: csv.DictReader) -> 'MCU':
        pins = []
        for row in reader:
            pin = Pin(
                position=row['Position'],
                name=row['Name'],
                pin_type=row['Type'],
            )
            pins.append(pin)
        return MCU(ref, info, pins)

    def pin_types(self) -> Set[str]:
        return {p.pin_type for p in self.pins}

    def get_pins_by_type(self, pin_type: str) -> List[Pin]:
        """
        Return all pins of that type, sorted.
        """
        pins = [p for p in self.pins if p.pin_type == pin_type]
        pins.sort(key=lambda p: (p.name, p.position))
        return pins

    def get_pin_names_by_type(self, pin_type: str) -> List[str]:
        """
        Return all pin names of that type (without duplicates), sorted.
        """
        pins = self.get_pins_by_type(pin_type)
        names = [p.name for p in pins]
        deduplicated = list(OrderedDict.fromkeys(names))
        return deduplicated

    @property
    def description(self) -> str:
        description = '{} self by ST Microelectronics.\\n\\n'.format(self.name)
        description += 'Package: {}\\nFlash: {}\\nRAM: {}\\nI/Os: {}\\nFrequency: {}\\n\\n'.format(
            self.package, self.flash, self.ram, self.io, self.frequency,
        )
        if self.boards:
            description += 'Available evalboards:\\n'
            for board in self.boards:
                description += '- {}\\n'.format(board)
            description += '\\n'
        description += 'Generated with {}'.format(generator)

    def generate_placement_data(self, debug: bool = False) -> SymbolPinPlacement:
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

        """
        # Ensure that only known pin types are present
        unknown_pin_types = self.pin_types() - {'Reset', 'Power', 'MonoIO', 'Boot', 'NC', 'I/O'}
        assert len(unknown_pin_types) == 0, 'Unknown pin types: {}'.format(unknown_pin_types)

        # Determine number of pins on both sides
        left_pins = [self.get_pin_names_by_type(t) for t in ['Reset', 'Power', 'MonoIO', 'Boot', 'NC']]
        left_pins = [group for group in left_pins if len(group) > 0]
        left_count = sum(len(group) for group in left_pins)
        right_pins = [self.get_pin_names_by_type(t) for t in ['I/O']]
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
                placement.add_left_pin(pin_name, y)
                y -= 1
        y = max_y
        for i, group in enumerate(right_pins):
            if i > 0:
                # Put a space between groups
                y -= 1
            for pin_name in group:
                placement.add_right_pin(pin_name, y)
                y -= 1
        placement.sort()

        if debug:
            print('Placement:')
            print('  Left:')
            for (pin_name, y) in placement.left:
                print('    {} {}'.format(y, pin_name))
            print('  Right:')
            for (pin_name, y) in placement.right:
                print('    {} {}'.format(y, pin_name))

        return placement

    def __str__(self) -> str:
        return '<MCU {} ({} pins, {})>'.format(self.name, len(self.pins), self.package)


def _make(dirpath: str) -> None:
    if not (path.exists(dirpath) and path.isdir(dirpath)):
        makedirs(dirpath)


def generate_symbol(mcu: MCU, data_dir: str, debug: bool = False):
    placement = mcu.generate_placement_data(debug)

    uuid_sym = uuid('sym', mcu.ref, 'sym')
    symbol = Symbol(
        uuid_sym,
        Name(mcu.name),
        Description(mcu.description),
        Keywords('stm32, stm, st, mcu, microcontroller, arm, cortex'),
        Author('Danilo Bargen, John Eaton'),
        Version('0.1'),
        Created('2020-01-30T20:55:23Z'),
        Category('22151601-c2d9-419a-87bc-266f9c7c3459'),
    )
    for pin_name, position, rotation in placement.pins(width, grid):
        symbol.add_pin(SymbolPin(
            uuid('sym', mcu.ref, 'pin-{}'.format(pin_name.lower())),
            Name(pin_name),
            position,
            rotation,
            Length(grid),
        ))
    polygon = Polygon(
        uuid('sym', mcu.ref, 'polygon'),
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
        uuid('sym', mcu.ref, 'text-name'),
        Layer('sym_names'),
        Value('{{NAME}}'),
        Align('left bottom'),
        Height(text_height),
        Position(-dx, max_y),
        Rotation(0.0),
    )
    text_value = Text(
        uuid('sym', mcu.ref, 'text-value'),
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

    print('Wrote sym for {} ({})'.format(mcu.ref, uuid_sym))


def generate(mcu_ref: str, data_dir: str, debug: bool = False):
    _make('out')
    _make('out/stm32')
    _make('out/stm32/sym')

    with open(path.join(data_dir, '{}.info.json'.format(mcu_ref)), 'r') as f:
        info = json.loads(f.read())

    with open(path.join(data_dir, '{}.pinout.csv'.format(mcu_ref)), 'r') as f:
        reader = csv.DictReader(f, delimiter=',', quotechar='"')
        mcu = MCU.from_dictreader(mcu_ref, info, reader)
        assert None not in mcu.pin_types()

    if debug:
        print()
        print('Processing {}'.format(mcu))
        print('Pin types: {}'.format(mcu.pin_types()))
        for pt in mcu.pin_types():
            print('# {}'.format(pt))
            for pin in mcu.get_pins_by_type(pt):
                print('  - {} [{}]'.format(pin.name, pin.position))

    generate_symbol(mcu, data_dir, debug)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate STM32 library elements')
    parser.add_argument(
        '--data-dir', metavar='path-to-data-dir', required=True,
        help='path to the data dir from https://github.com/LibrePCB/stm32-pinout',
    )
    parser.add_argument(
        '--mcu', metavar='mcu-ref',
        help='only process the specified MCU',
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='print debug information',
    )
    args = parser.parse_args()

    if args.mcu:
        generate(args.mcu, args.data_dir, args.debug)
    else:
        for filename in listdir(args.data_dir):
            match = re.match(r'(STM32.*)\.pinout\.csv$', filename)
            if match:
                mcu = match.group(1)
                generate(mcu, args.data_dir, args.debug)

    save_cache(uuid_cache_file, uuid_cache)
