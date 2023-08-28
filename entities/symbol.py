from os import makedirs, path

from typing import List

from common import format_float

from .common import (
    Author, Category, Circle, Created, Deprecated, Description, FloatValue, GeneratedBy, Keywords, Length, Name,
    Polygon, Position, Rotation, Text, Version
)
from .helper import indent_entities


class NamePosition():
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __str__(self) -> str:
        return '(name_position {} {})'.format(format_float(self.x), format_float(self.y))


class NameRotation(FloatValue):
    def __init__(self, rotation: float):
        super().__init__('name_rotation', rotation)


class NameHeight(FloatValue):
    def __init__(self, height: float):
        super().__init__('name_height', height)


class NameAlign():
    def __init__(self, align: str):
        self.align = align

    def __str__(self) -> str:
        return '(name_align {})'.format(self.align)


class Pin():
    def __init__(self, uuid: str, name: Name, position: Position,
                 rotation: Rotation, length: Length,
                 name_position: NamePosition, name_rotation: NameRotation,
                 name_height: NameHeight, name_align: NameAlign):
        self.uuid = uuid
        self.name = name
        self.position = position
        self.rotation = rotation
        self.length = length
        self.name_position = name_position
        self.name_rotation = name_rotation
        self.name_height = name_height
        self.name_align = name_align

    def __str__(self) -> str:
        return '(pin {} {}\n'.format(self.uuid, self.name) +\
            ' {} {} {}\n'.format(self.position, self.rotation, self.length) +\
            ' {} {} {}\n'.format(self.name_position, self.name_rotation, self.name_height) +\
            ' {}\n'.format(self.name_align) +\
            ')'


class Symbol:
    def __init__(self, uuid: str, name: Name, description: Description,
                 keywords: Keywords, author: Author, version: Version,
                 created: Created, deprecated: Deprecated,
                 generated_by: GeneratedBy, category: Category,):
        self.uuid = uuid
        self.name = name
        self.description = description
        self.keywords = keywords
        self.author = author
        self.version = version
        self.created = created
        self.deprecated = deprecated
        self.generated_by = generated_by
        self.category = category
        self.pins = []  # type: List[Pin]
        self.polygons = []  # type: List[Polygon]
        self.circles = []  # type: List[Circle]
        self.texts = []  # type: List[Text]

    def add_pin(self, pin: Pin) -> None:
        self.pins.append(pin)

    def add_polygon(self, polygon: Polygon) -> None:
        self.polygons.append(polygon)

    def add_circle(self, circle: Circle) -> None:
        self.circles.append(circle)

    def add_text(self, text: Text) -> None:
        self.texts.append(text)

    def __str__(self) -> str:
        ret = '(librepcb_symbol {}\n'.format(self.uuid) +\
            ' {}\n'.format(self.name) +\
            ' {}\n'.format(self.description) +\
            ' {}\n'.format(self.keywords) +\
            ' {}\n'.format(self.author) +\
            ' {}\n'.format(self.version) +\
            ' {}\n'.format(self.created) +\
            ' {}\n'.format(self.deprecated) +\
            ' {}\n'.format(self.generated_by) +\
            ' {}\n'.format(self.category)
        ret += indent_entities(self.pins)
        ret += indent_entities(self.polygons)
        ret += indent_entities(self.circles)
        ret += indent_entities(self.texts)
        ret += ')'
        return ret

    def serialize(self, output_directory: str) -> None:
        dir_path = path.join(output_directory, self.uuid)
        if not (path.exists(dir_path) and path.isdir(dir_path)):
            makedirs(dir_path)
        with open(path.join(dir_path, '.librepcb-sym'), 'w') as f:
            f.write('1\n')
        with open(path.join(dir_path, 'symbol.lp'), 'w') as f:
            f.write(str(self))
            f.write('\n')
