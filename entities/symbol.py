from typing import List

from .common import (
    Author, Category, Circle, Created, Deprecated, Description, Keywords, Length, Name, Polygon, Position, Rotation, Text,
    Version
)
from .helper import indent_entities


class Pin():
    def __init__(self, uuid: str, name: Name, position: Position, rotation: Rotation, length: Length):
        self.uuid = uuid
        self.name = name
        self.position = position
        self.rotation = rotation
        self.length = length

    def __str__(self) -> str:
        return '(pin {} {}\n'.format(self.uuid, self.name) +\
            ' {} {} {}\n'.format(self.position, self.rotation, self.length) +\
            ')'


class Symbol:
    def __init__(self, uuid: str, name: Name, description: Description,
                 keywords: Keywords, author: Author, version: Version,
                 created: Created, category: Category,
                 deprecated: Deprecated = Deprecated(False)):
        self.uuid = uuid
        self.name = name
        self.description = description
        self.keywords = keywords
        self.author = author
        self.version = version
        self.created = created
        self.deprecated = deprecated
        self.category = category
        self.pins = []  # type: List[Pin]
        self.polygons = []  # type: List[Polygon]
        self.circles = []  # type: List[Circle]
        self.texts = []  # type: List[Text]

    def add_pin(self, pin: Pin) -> None:
        self.pins.append(pin)

    def add_polygon(self, polygon: Polygon) -> None:
        self.polygons.append(polygon)

    def add_text(self, text: Text) -> None:
        self.texts.append(text)

    def add_circle(self, circle: Circle) -> None:
        self.circles.append(circle)

    def __str__(self) -> str:
        ret = '(librepcb_symbol {}\n'.format(self.uuid) +\
            ' {}\n'.format(self.name) +\
            ' {}\n'.format(self.description) +\
            ' {}\n'.format(self.keywords) +\
            ' {}\n'.format(self.author) +\
            ' {}\n'.format(self.version) +\
            ' {}\n'.format(self.created) +\
            ' {}\n'.format(self.deprecated) +\
            ' {}\n'.format(self.category)
        ret += indent_entities(self.pins)
        ret += indent_entities(self.polygons)
        ret += indent_entities(self.circles)
        ret += indent_entities(self.texts)
        ret += ')'
        return ret
