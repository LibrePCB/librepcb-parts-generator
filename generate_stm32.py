"""
Generate STM32 microcontroller symbols, components and devices.

TODO: More information about data source.

"""
import csv
import math
import re
from typing import Iterable, Optional, Set, List, Tuple


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
    def __init__(self):
        self.left = []  # type: List[Tuple[Pin, int]]
        self.right = []  # type: List[Tuple[Pin, int]]

    def add_left_pin(self, pin: Pin, y_pos: int):
        self.left.append((pin, y_pos))

    def add_right_pin(self, pin: Pin, y_pos: int):
        self.right.append((pin, y_pos))

    def sort(self):
        """
        Sort pins in-place by y-position.
        """
        self.left.sort(key=lambda x: -x[1])
        self.right.sort(key=lambda x: -x[1])


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
        Return all pins of that type, sorted alphanumerically.
        """
        pins = [p for p in self.pins if p.pin_type == pin_type]
        pins.sort(key=lambda p: (p.name, p.number))
        return pins

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
        left_pins = [self.get_pins_by_type(t) for t in ['Reset', 'Power', 'MonoIO', 'NC']]
        left_pins = [group for group in left_pins if len(group) > 0]
        left_count = sum(len(group) for group in left_pins)
        right_pins = [self.get_pins_by_type(t) for t in ['I/O']]
        right_pins = [group for group in right_pins if len(group) > 0]
        right_count = sum(len(group) for group in right_pins)
        height = max([left_count + len(left_pins) - 1, right_count + len(right_pins) - 1])
        max_y = math.ceil(height / 2)
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
            for pin in group:
                placement.add_left_pin(pin, y)
                y -= 1
        y = max_y
        for i, group in enumerate(right_pins):
            if i > 0:
                # Put a space between groups
                y -= 1
            for pin in group:
                placement.add_right_pin(pin, y)
                y -= 1
        placement.sort()

        print('Placement:')
        print('  Left:')
        for (pin, y) in placement.left:
            print('    {} {}'.format(y, pin.name))
        print('  Right:')
        for (pin, y) in placement.right:
            print('    {} {}'.format(y, pin.name))

        return placement

    def __str__(self) -> str:
        return '<MCU {} ({} pins)>'.format(self.name, len(self.pins))


name = 'STM32WB55CEUx'
with open('stm32/data/{}.txt'.format(name)) as f:
    reader = csv.DictReader(f, delimiter=',', quotechar='"')
    mcu = MCU.from_dictreader(name, reader)
    assert None not in mcu.pin_types()

print(mcu)
print('Pin types: {}'.format(mcu.pin_types()))
for pt in mcu.pin_types():
    print('# {}'.format(pt))
    for pin in mcu.get_pins_by_type(pt):
        print('  - {} [{}]'.format(pin.name, pin.number))


print()
mcu.generate_placement_data()
