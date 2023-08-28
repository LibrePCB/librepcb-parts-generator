from os import makedirs, path

from typing import List

from .common import Author, Category, Created, Deprecated, Description, GeneratedBy, Keywords, Name, UUIDValue, Version
from .component import SignalUUID
from .helper import indent_entities


class ComponentUUID(UUIDValue):
    def __init__(self, component_uuid: str):
        super().__init__('component', component_uuid)


class PackageUUID(UUIDValue):
    def __init__(self, package_uuid: str):
        super().__init__('package', package_uuid)


class ComponentPad():
    def __init__(self, pad_uuid: str, signal: SignalUUID):
        self.pad_uuid = pad_uuid
        self.signal = signal

    def __str__(self) -> str:
        return '(pad {} {})'.format(self.pad_uuid, self.signal)


class Device():
    def __init__(self, uuid: str, name: Name, description: Description,
                 keywords: Keywords, author: Author, version: Version,
                 created: Created, deprecated: Deprecated,
                 generated_by: GeneratedBy, category: Category,
                 component_uuid: ComponentUUID, package_uuid: PackageUUID):
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
        self.component_uuid = component_uuid
        self.package_uuid = package_uuid
        self.pads = []  # type: List[ComponentPad]

    def add_pad(self, pad: ComponentPad) -> None:
        self.pads.append(pad)

    def __str__(self) -> str:
        ret = '(librepcb_device {}\n'.format(self.uuid) +\
            ' {}\n'.format(self.name) +\
            ' {}\n'.format(self.description) +\
            ' {}\n'.format(self.keywords) +\
            ' {}\n'.format(self.author) +\
            ' {}\n'.format(self.version) +\
            ' {}\n'.format(self.created) +\
            ' {}\n'.format(self.deprecated) +\
            ' {}\n'.format(self.generated_by) +\
            ' {}\n'.format(self.category) +\
            ' {}\n'.format(self.component_uuid) +\
            ' {}\n'.format(self.package_uuid)
        ret += indent_entities(sorted(self.pads, key=lambda x: str(x.pad_uuid)))
        ret += ')'
        return ret

    def serialize(self, output_directory: str) -> None:
        dir_path = path.join(output_directory, self.uuid)
        if not (path.exists(dir_path) and path.isdir(dir_path)):
            makedirs(dir_path)
        with open(path.join(dir_path, '.librepcb-dev'), 'w') as f:
            f.write('1\n')
        with open(path.join(dir_path, 'device.lp'), 'w') as f:
            f.write(str(self))
            f.write('\n')
