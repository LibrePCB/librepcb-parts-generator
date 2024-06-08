from typing import Iterable, List, Optional

from common import escape_string, serialize_common
from entities.attribute import Attribute

from .common import (
    Author, Category, Created, Deprecated, Description, GeneratedBy, Keywords, Name, StringValue, UUIDValue, Version
)
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


class Manufacturer(StringValue):
    def __init__(self, manufacturer: str):
        super().__init__('manufacturer', manufacturer)


class Part():
    def __init__(self, mpn: str, manufacturer: Manufacturer, attributes: Optional[List[Attribute]] = None):
        self.mpn = mpn
        self.manufacturer = manufacturer
        self.attributes = attributes or []

    def __str__(self) -> str:
        ret = '(part "{}" {}\n'.format(escape_string(self.mpn), self.manufacturer)
        ret += indent_entities(self.attributes)
        ret += ')'
        return ret

    def add_attribute(self, attr: Attribute) -> None:
        self.attributes.append(attr)


class Device():
    def __init__(self, uuid: str, name: Name, description: Description,
                 keywords: Keywords, author: Author, version: Version,
                 created: Created, deprecated: Deprecated,
                 generated_by: GeneratedBy, categories: Iterable[Category],
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
        self.categories = categories
        self.component_uuid = component_uuid
        self.package_uuid = package_uuid
        self.pads: List[ComponentPad] = []
        self.parts: List[Part] = []
        self.approvals: List[str] = []

    def add_pad(self, pad: ComponentPad) -> None:
        self.pads.append(pad)

    def add_part(self, part: Part) -> None:
        self.parts.append(part)

    def add_approval(self, approval: str) -> None:
        self.approvals.append(approval)

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
            ''.join([' {}\n'.format(cat) for cat in self.categories]) +\
            ' {}\n'.format(self.component_uuid) +\
            ' {}\n'.format(self.package_uuid)
        ret += indent_entities(sorted(self.pads, key=lambda x: str(x.pad_uuid)))
        ret += indent_entities(self.parts)
        ret += indent_entities(sorted(self.approvals))
        ret += ')'
        return ret

    def serialize(self, output_directory: str) -> None:
        serialize_common(
            serializable=self,
            output_directory=output_directory,
            uuid=self.uuid,
            long_type='device',
            short_type='dev'
        )
