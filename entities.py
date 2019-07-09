"""
LibrePCB S-expression entities
"""

from common import format_float
from typing import List


class DateValue(object):
    """Helper class to represent a single named date value"""
    def __init__(self, name: str, date: str):
        self.name = name
        self.date = date

    def __str__(self) -> str:
        return '({} {})'.format(self.name, self.date)


class UUIDValue(object):
    """Helper class to represent a single named UUID value"""
    def __init__(self, name: str, uuid: str):
        self.name = name
        self.uuid = uuid

    def __str__(self) -> str:
        return '({} {})'.format(self.name, self.uuid)


class BoolValue(object):
    """Helper class to represent a single named boolean value"""
    def __init__(self, name: str, value: bool):
        self.name = name
        self.value = str(value).lower()

    def __str__(self) -> str:
        return '({} {})'.format(self.name, self.value)


class StringValue(object):
    """Helper class to represent a single named string value"""
    def __init__(self, name: str, value: str):
        self.name = name
        self.value = value

    def __str__(self) -> str:
        return '({} "{}")'.format(self.name, self.value)


class FloatValue(object):
    """Helper class to represent a single named float value"""
    def __init__(self, name: str, value: float):
        self.name = name
        self.value = value

    def __str__(self) -> str:
        return '({} {})'.format(self.name, format_float(self.value))


class Name(StringValue):
    def __init__(self, name: str):
        super().__init__('name', name)


class Description(StringValue):
    def __init__(self, description: str):
        super().__init__('description', description)


class Keywords(StringValue):
    def __init__(self, keywords: str):
        super().__init__('keywords', keywords)


class Author(StringValue):
    def __init__(self, author: str):
        super().__init__('author', author)


class Version(StringValue):
    def __init__(self, version: str):
        super().__init__('version', version)


class Created(DateValue):
    def __init__(self, created: str):
        super().__init__('created', created)


class Deprecated(BoolValue):
    def __init__(self, deprecated: bool):
        super().__init__('deprecated', deprecated)


class Category(UUIDValue):
    def __init__(self, category: str):
        super().__init__('category', category)


class Position(object):
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __str__(self) -> str:
        return '(position {} {})'.format(self.x, self.y)


class Rotation(FloatValue):
    def __init__(self, rotation: float):
        super().__init__('rotation', rotation)


class Length(FloatValue):
    def __init__(self, length: float):
        super().__init__('length', length)


class SchematicsPin(object):
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


class Width(FloatValue):
    def __init__(self, width: float):
        super().__init__('width', width)


class Height(FloatValue):
    def __init__(self, height: float):
        super().__init__('height', height)


class Angle(FloatValue):
    def __init__(self, angle: float):
        super().__init__('angle', angle)


class Fill(BoolValue):
    def __init__(self, fill: bool):
        super().__init__('fill', fill)


class GrabArea(BoolValue):
    def __init__(self, grab_area: bool):
        super().__init__('grab_area', grab_area)


class Vertex(object):
    def __init__(self, position: Position, angle: Angle):
        self.position = position
        self.angle = angle

    def __str__(self) -> str:
        return '(vertex {} {})'.format(self.position, self.angle)


class Layer(object):
    def __init__(self, layer: str):
        self.layer = layer

    def __str__(self) -> str:
        return '(layer {})'.format(self.layer)


class Polygon(object):
    def __init__(self, uuid: str, layer: Layer, width: Width, fill: Fill, grab_area: GrabArea):
        self.uuid = uuid
        self.layer = layer
        self.width = width
        self.fill = fill
        self.grab_area = grab_area
        self.vertices = []  # type: List[Vertex]

    def add_vertex(self, vertex: Vertex) -> None:
        self.vertices.append(vertex)

    def __str__(self) -> str:
        ret = '(polygon {} {}\n'.format(self.uuid, self.layer) +\
            ' {} {} {}\n'.format(self.width, self.fill, self.grab_area)
        for vertex in self.vertices:
            ret += ' {}\n'.format(vertex)
        ret += ')'
        return ret


class Value(StringValue):
    def __init__(self, value: str):
        super().__init__('value', value)


class Align(object):
    def __init__(self, align: str):
        self.align = align

    def __str__(self) -> str:
        return '(align {})'.format(self.align)


class Text(object):
    def __init__(self, uuid: str, layer: Layer, value: Value, align: Align, height: Height, position: Position, rotation: Rotation):
        self.uuid = uuid
        self.layer = layer
        self.value = value
        self.align = align
        self.height = height
        self.position = position
        self.rotation = rotation

    def __str__(self) -> str:
        return '(text {} {} {}\n'.format(self.uuid, self.layer, self.value) +\
               ' {} {} {} {}\n'.format(self.align, self.height, self.position, self.rotation) +\
               ')'
