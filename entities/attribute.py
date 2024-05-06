from typing import Optional

from entities.common import EnumValue, Value


class AttributeUnit(EnumValue):
    def get_name(self) -> str:
        return 'unit'


class UnitlessUnit(AttributeUnit):
    NONE = "none"


class AttributeType(EnumValue):
    VOLTAGE = 'voltage'
    STRING = 'string'
    CURRENT = 'current'
    RESISTANCE = 'resistance'
    CAPACITANCE = 'capacitance'
    POWER = 'power'
    INDUCTANCE = 'inductance'
    FREQUENCY = 'frequency'

    def get_name(self) -> str:
        return 'type'


class Attribute():
    def __init__(self, name: str, value: Value | str, attribute_type: AttributeType, unit: Optional[AttributeUnit]) -> None:
        self.name = name

        self.value = Value(value) if isinstance(value, str) else value
        self.unit = unit or UnitlessUnit.NONE
        self.attribute_type = attribute_type

    def __str__(self) -> str:
        return '(attribute "{}" {} {} {})'.format(self.name, self.attribute_type, self.unit, self.value)


class CapacitanceUnit(AttributeUnit):
    PICOFARAD = 'picofarad'
    NANOFARAD = 'nanofarad'
    MICROFARAD = 'microfarad'
    MILLIFARAD = 'millifarad'
    FARAD = 'farad'


class CapacitanceAttribute(Attribute):
    def __init__(self, name: str, value: Value | str, unit: CapacitanceUnit) -> None:
        super().__init__(name, value, AttributeType.CAPACITANCE, unit)


class CurrentUnit(AttributeUnit):
    PICOAMPERE = 'picoampere'
    NANOAMPERE = 'nanoampere'
    MICROAMPERE = 'microampere'
    MILLIAMPERE = 'milliampere'
    AMPERE = 'ampere'
    KILOAMPERE = 'kiloampere'
    MEGAAMPERE = 'megaampere'


class CurrentAttribute(Attribute):
    def __init__(self, name: str, value: Value | str, unit: CurrentUnit) -> None:
        super().__init__(name, value, AttributeType.CURRENT, unit)


class FrequencyUnit(AttributeUnit):
    MICROHERTZ = 'microhertz'
    MILLIHERTZ = 'millihertz'
    HERTZ = 'hertz'
    KILOHERTZ = 'kilohertz'
    MEGAHERTZ = 'megahertz'
    GIGAHERTZ = 'gigahertz'


class FrequencyAttribute(Attribute):
    def __init__(self, name: str, value: Value | str, unit: FrequencyUnit) -> None:
        super().__init__(name, value, AttributeType.FREQUENCY, unit)


class InductanceUnit(AttributeUnit):
    NANOHENRY = 'nanohenry'
    MICROHENRY = 'microhenry'
    MILLIHENRY = 'millihenry'
    HENRY = 'henry'


class InductanceAttribute(Attribute):
    def __init__(self, name: str, value: Value | str, unit: InductanceUnit) -> None:
        super().__init__(name, value, AttributeType.INDUCTANCE, unit)


class PowerUnit(AttributeUnit):
    NANOWATT = 'nanowatt'
    MICROWATT = 'microwatt'
    MILLIWATT = 'milliwatt'
    WATT = 'watt'
    KILOWATT = 'kilowatt'
    MEGAWATT = 'megawatt'
    GIGAWATT = 'gigawatt'


class PowerAttribute(Attribute):
    def __init__(self, name: str, value: Value | str, unit: PowerUnit) -> None:
        super().__init__(name, value, AttributeType.POWER, unit)


class ResistanceUnit(AttributeUnit):
    MICROOHM = 'microohm'
    MILLIOHM = 'milliohm'
    OHM = 'ohm'
    KILOOHM = 'kiloohm'
    MEGAOHM = 'megaohm'


class ResistanceAttribute(Attribute):
    def __init__(self, name: str, value: Value | str, unit: ResistanceUnit) -> None:
        super().__init__(name, value, AttributeType.RESISTANCE, unit)


class VoltageUnit(AttributeUnit):
    NANOVOLT = 'nanovolt'
    MICROVOLT = 'microvolt'
    MILLIVOLT = 'millivolt'
    VOLT = 'volt'
    KILOVOLT = 'kilovolt'
    MEGAVOLT = 'megavolt'


class VoltageAttribute(Attribute):
    def __init__(self, name: str, value: Value | str, unit: VoltageUnit) -> None:
        super().__init__(name, value, AttributeType.VOLTAGE, unit)


class StringAttribute(Attribute):
    def __init__(self, name: str, value: Value | str) -> None:
        super().__init__(name, value, AttributeType.STRING, None)
