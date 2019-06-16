"""
LibrePCB S-expression entities
"""


class Position(object):
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def to_s_exp(self) -> str:
        return '(position {} {})'.format(self.x, self.y)


class Rotation(object):
    def __init__(self, rotation: float):
        self.rotation = rotation

    def to_s_exp(self) -> str:
        return '(rotation {})'.format(self.rotation)


class Length(object):
    def __init__(self, length: float):
        self.length = length

    def to_s_exp(self) -> str:
        return '(length {})'.format(self.length)


class SchematicsPin(object):
    def __init__(self, uuid: str, name: str, position: Position, rotation: Rotation, length: Length):
        self.uuid = uuid
        self.name = name
        self.position = position
        self.rotation = rotation
        self.length = length

    def to_s_exp(self) -> [str]:
        return [
            '(pin {} (name "{}")'.format(self.uuid, self.name),
            ' {} {} {}'.format(self.position.to_s_exp(), self.rotation.to_s_exp(), self.length.to_s_exp()),
            ')',
        ]
