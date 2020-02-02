"""
Generate STM32 microcontroller symbols, components and devices.

TODO: More information about data source.

"""
import csv
import math
import re
from collections import OrderedDict
from os import makedirs, path
from uuid import uuid4

from typing import Iterable, List, Optional, Set, Tuple

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

# Enable debug printing
DEBUG = False

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
        number: int,
        name: str,
        pin_type: str,
    ):
        self.number = number
        self.name = name
        self.pin_type = pin_type

    def classify(self) -> Optional[str]:
        """
        Classify a pin into one of the following classes:

        - reset
        - power
        - oscillator

        TODO Remove?

        If the class cannot be determined, return `None`.

        """
        if 'RST' in self.name:
            return 'reset'
        if re.match(r'^V(BAT|CC|DD|SS)', self.name):
            return 'power'
        return None


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
    def __init__(self, name: str, pins: Iterable[Pin]):
        self.name = name
        self.pins = list(pins)

    @staticmethod
    def from_dictreader(name: str, reader: csv.DictReader) -> 'MCU':
        pins = []
        for row in reader:
            pin = Pin(
                number=int(row['Position']),
                name=row['Name'],
                pin_type=row['Type'],
            )
            pins.append(pin)
        return MCU(name, pins)

    def pin_types(self) -> Set[str]:
        return {p.pin_type for p in self.pins}

    def get_pins_by_type(self, pin_type: str) -> List[Pin]:
        """
        Return all pins of that type, sorted.
        """
        pins = [p for p in self.pins if p.pin_type == pin_type]
        pins.sort(key=lambda p: (p.name, p.number))
        return pins

    def get_pin_names_by_type(self, pin_type: str) -> List[str]:
        """
        Return all pin names of that type (without duplicates), sorted.
        """
        pins = self.get_pins_by_type(pin_type)
        names = [p.name for p in pins]
        deduplicated = list(OrderedDict.fromkeys(names))
        return deduplicated

    def generate_placement_data(self) -> SymbolPinPlacement:
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
        | NC           |
        +--------------+

        """
        # Ensure that only known pin types are present
        unknown_pin_types = self.pin_types() - {'Reset', 'Power', 'MonoIO', 'NC', 'I/O'}
        assert len(unknown_pin_types) == 0, 'Unknown pin types: {}'.format(unknown_pin_types)

        # Determine number of pins on both sides
        left_pins = [self.get_pin_names_by_type(t) for t in ['Reset', 'Power', 'MonoIO', 'NC']]
        left_pins = [group for group in left_pins if len(group) > 0]
        left_count = sum(len(group) for group in left_pins)
        right_pins = [self.get_pin_names_by_type(t) for t in ['I/O']]
        right_pins = [group for group in right_pins if len(group) > 0]
        right_count = sum(len(group) for group in right_pins)
        height = max([left_count + len(left_pins) - 1, right_count + len(right_pins) - 1])
        max_y = math.ceil(height / 2)
        if DEBUG:
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

        if DEBUG:
            print('Placement:')
            print('  Left:')
            for (pin_name, y) in placement.left:
                print('    {} {}'.format(y, pin_name))
            print('  Right:')
            for (pin_name, y) in placement.right:
                print('    {} {}'.format(y, pin_name))

        return placement

    def __str__(self) -> str:
        return '<MCU {} ({} pins)>'.format(self.name, len(self.pins))


if __name__ == '__main__':
    def _make(dirpath: str) -> None:
        if not (path.exists(dirpath) and path.isdir(dirpath)):
            makedirs(dirpath)
    _make('out')
    _make('out/stm32')
    _make('out/stm32/sym')

    mcu_name = 'STM32WB55CEUx'
    with open('stm32/data/{}.txt'.format(mcu_name)) as f:
        reader = csv.DictReader(f, delimiter=',', quotechar='"')
        mcu = MCU.from_dictreader(mcu_name, reader)
        assert None not in mcu.pin_types()

    if DEBUG:
        print(mcu)
        print('Pin types: {}'.format(mcu.pin_types()))
        for pt in mcu.pin_types():
            print('# {}'.format(pt))
            for pin in mcu.get_pins_by_type(pt):
                print('  - {} [{}]'.format(pin.name, pin.number))

    placement = mcu.generate_placement_data()

    uuid_sym = uuid('sym', mcu_name, 'sym')
    symbol = Symbol(
        uuid_sym,
        Name(mcu_name),
        Description(
            '{} MCU by ST Microelectronics.\\n\\nGenerated with {}'.format(
                mcu_name, generator,
            )
        ),
        Keywords('stm32, stm, st, mcu, microcontroller, arm, cortex'),
        Author('Danilo Bargen, John Eaton'),
        Version('0.1'),
        Created('2020-01-30T20:55:23Z'),
        Category('22151601-c2d9-419a-87bc-266f9c7c3459'),
    )
    for pin_name, position, rotation in placement.pins(width, grid):
        symbol.add_pin(SymbolPin(
            uuid('sym', mcu_name, 'pin-{}'.format(pin_name.lower())),
            Name(pin_name),
            position,
            rotation,
            Length(grid),
        ))
    polygon = Polygon(
        uuid('sym', mcu_name, 'polygon'),
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
        uuid('sym', mcu_name, 'text-name'),
        Layer('sym_names'),
        Value('{{NAME}}'),
        Align('left bottom'),
        Height(text_height),
        Position(-dx, max_y),
        Rotation(0.0),
    )
    text_value = Text(
        uuid('sym', mcu_name, 'text-value'),
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

    print('Wrote symbol {} ({})'.format(mcu_name, uuid_sym))

    save_cache(uuid_cache_file, uuid_cache)
