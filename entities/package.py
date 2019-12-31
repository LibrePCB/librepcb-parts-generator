from typing import List

from common import format_float

from .common import (
    Align, Author, BoolValue, Category, Circle, Created, Deprecated, Description, EnumValue, FloatValue, Height,
    Keywords, Layer, Name, Polygon, Position, Rotation, Value, Version
)
from .helper import indent_entities


class PackagePad():
    def __init__(self, uuid: str, name: Name):
        self.uuid = uuid
        self.name = name

    def __str__(self) -> str:
        return '(pad {} {})'.format(self.uuid, self.name)


class StrokeWidth(FloatValue):
    def __init__(self, stroke_width: float):
        super().__init__('stroke_width', stroke_width)


class LetterSpacing(EnumValue):
    AUTO = 'auto'

    def get_name(self) -> str:
        return 'letter_spacing'


class LineSpacing(EnumValue):
    AUTO = 'auto'

    def get_name(self) -> str:
        return 'line_spacing'


class AutoRotate(BoolValue):
    def __init__(self, auto_rotate: bool):
        super().__init__('auto_rotate', auto_rotate)


class Mirror(BoolValue):
    def __init__(self, mirror: bool):
        super().__init__('mirror', mirror)


class StrokeText():
    def __init__(self, uuid: str, layer: Layer, height: Height,
                 stroke_width: StrokeWidth, letter_spacing: LetterSpacing,
                 line_spacing: LineSpacing, align: Align, position: Position,
                 rotation: Rotation, auto_rotate: AutoRotate, mirror: Mirror,
                 value: Value):
        self.uuid = uuid
        self.layer = layer
        self.height = height
        self.stroke_width = stroke_width
        self.letter_spacing = letter_spacing
        self.line_spacing = line_spacing
        self.align = align
        self.position = position
        self.rotation = rotation
        self.auto_rotate = auto_rotate
        self.mirror = mirror
        self.value = value

    def __str__(self) -> str:
        ret = '(stroke_text {} {}\n'.format(self.uuid, self.layer) +\
            ' {} {} {} {}\n'.format(self.height, self.stroke_width, self.letter_spacing, self.line_spacing) +\
            ' {} {} {}\n'.format(self.align, self.position, self.rotation) +\
            ' {} {} {}\n)'.format(self.auto_rotate, self.mirror, self.value)
        return ret


class Side(EnumValue):
    TOP = 'top'
    BOTTOM = 'bottom'
    THT = 'tht'

    def get_name(self) -> str:
        return 'side'


class Shape(EnumValue):
    ROUND = 'round'
    RECT = 'rect'
    OCTAGON = 'octagon'

    def get_name(self) -> str:
        return 'shape'


class Size():
    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height

    def __str__(self) -> str:
        return '(size {} {})'.format(format_float(self.width), format_float(self.height))


class Drill(FloatValue):
    def __init__(self, drill: float):
        super().__init__('drill', drill)


class FootprintPad():
    def __init__(self, uuid: str, side: Side, shape: Shape, position: Position,
                 rotation: Rotation, size: Size, drill: Drill):
        self.uuid = uuid
        self.side = side
        self.shape = shape
        self.position = position
        self.rotation = rotation
        self.size = size
        self.drill = drill

    def __str__(self) -> str:
        ret = '(pad {} {} {}\n'.format(self.uuid, self.side, self.shape) +\
            ' {} {} {} {}\n)'.format(self.position, self.rotation, self.size, self.drill)
        return ret


class Footprint():
    def __init__(self, uuid: str, name: Name, description: Description):
        self.uuid = uuid
        self.name = name
        self.description = description
        self.pads = []  # type: List[FootprintPad]
        self.polygons = []  # type: List[Polygon]
        self.circles = []  # type: List[Circle]
        self.texts = []  # type: List[StrokeText]

    def add_pad(self, pad: FootprintPad) -> None:
        self.pads.append(pad)

    def add_polygon(self, polygon: Polygon) -> None:
        self.polygons.append(polygon)

    def add_circle(self, circle: Circle) -> None:
        self.circles.append(circle)

    def add_text(self, text: StrokeText) -> None:
        self.texts.append(text)

    def __str__(self) -> str:
        ret = '(footprint {}\n'.format(self.uuid) +\
            ' {}\n'.format(self.name) +\
            ' {}\n'.format(self.description)
        ret += indent_entities(self.pads)
        ret += indent_entities(self.polygons)
        ret += indent_entities(self.circles)
        ret += indent_entities(self.texts)
        ret += ')'
        return ret


class Package:
    def __init__(self, uuid: str, name: Name, description: Description,
                 keywords: Keywords, author: Author, version: Version,
                 created: Created, deprecated: Deprecated, category: Category):
        self.uuid = uuid
        self.name = name
        self.description = description
        self.keywords = keywords
        self.author = author
        self.version = version
        self.created = created
        self.deprecated = deprecated
        self.category = category
        self.pads = []  # type: List[PackagePad]
        self.footprints = []  # type: List[Footprint]

    def add_pad(self, pad: PackagePad) -> None:
        self.pads.append(pad)

    def add_footprint(self, footprint: Footprint) -> None:
        self.footprints.append(footprint)

    def __str__(self) -> str:
        ret = '(librepcb_package {}\n'.format(self.uuid) +\
            ' {}\n'.format(self.name) +\
            ' {}\n'.format(self.description) +\
            ' {}\n'.format(self.keywords) +\
            ' {}\n'.format(self.author) +\
            ' {}\n'.format(self.version) +\
            ' {}\n'.format(self.created) +\
            ' {}\n'.format(self.deprecated) +\
            ' {}\n'.format(self.category)
        ret += indent_entities(self.pads)
        ret += indent_entities(self.footprints)
        ret += ')'
        return ret
