from .common import Name, Position, Rotation, Length


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
