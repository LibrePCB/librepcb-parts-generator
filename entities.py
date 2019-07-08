"""
LibrePCB S-expression entities
"""


class Position(object):
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __str__(self) -> str:
        return '(position {} {})'.format(self.x, self.y)


class Rotation(object):
    def __init__(self, rotation: float):
        self.rotation = rotation

    def __str__(self) -> str:
        return '(rotation {})'.format(self.rotation)


class Length(object):
    def __init__(self, length: float):
        self.length = length

    def __str__(self) -> str:
        return '(length {})'.format(self.length)


class SchematicsPin(object):
    def __init__(self, uuid: str, name: str, position: Position, rotation: Rotation, length: Length):
        self.uuid = uuid
        self.name = name
        self.position = position
        self.rotation = rotation
        self.length = length

    def __str__(self) -> str:
        return '(pin {} (name "{}")\n'.format(self.uuid, self.name) +\
            ' {} {} {}\n'.format(self.position, self.rotation, self.length) +\
            ')'
