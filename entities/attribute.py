from enum import Enum

from entities.common import EnumValue, Value


class Unit(Enum):
    FARAD = 'farad'
    AMPERE = 'ampere'
    VOLT = 'volt'
    HENRY = 'henry'
    WATT = 'watt'
    HERTZ = 'hertz'
    OHM = 'ohm'
    NONE = 'none'


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

    def to_unit(self) -> Unit:
        if self == AttributeType.VOLTAGE:
            return Unit.VOLT
        elif self == AttributeType.CURRENT:
            return Unit.AMPERE
        elif self == AttributeType.FREQUENCY:
            return Unit.HERTZ
        elif self == AttributeType.RESISTANCE:
            return Unit.OHM
        elif self == AttributeType.STRING:
            return Unit.NONE
        elif self == AttributeType.INDUCTANCE:
            return Unit.HENRY
        elif self == AttributeType.POWER:
            return Unit.WATT
        else:
            return Unit.NONE  # Type.STRING and fallback


class MetricPrefix(Enum):
    PICO = 'pico'
    NANO = 'nano'
    MICRO = 'micro'
    MILLI = 'milli'
    NONE = ''  # no prefix
    KILO = 'kilo'
    MEGA = 'mega'
    GIGA = 'giga'


class AttributeUnit():
    def __init__(self, prefix: MetricPrefix, unit: Unit) -> None:
        self.attribute_unit = prefix.value + unit.value

    def __str__(self) -> str:
        return '(unit {})'.format(self.attribute_unit)


class Attribute():
    def __init__(self, name: str, value: Value, attribute_type: AttributeType, prefix: MetricPrefix) -> None:
        self.name = name
        self.value = value
        self.prefix = prefix if prefix is not None else MetricPrefix.NONE
        self.attribute_type = attribute_type if attribute_type is not None else AttributeType.STRING
        self.unit = AttributeUnit(self.prefix, self.attribute_type.to_unit())

    def __str__(self) -> str:
        return '(attribute "{}" {} {} {})'.format(self.name, self.attribute_type, self.unit, self.value)
