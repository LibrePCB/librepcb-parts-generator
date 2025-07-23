from typing import Optional

import pytest

from entities.attribute import (
    Attribute,
    AttributeType,
    AttributeUnit,
    CapacitanceAttribute,
    CapacitanceUnit,
    CurrentAttribute,
    CurrentUnit,
    FrequencyAttribute,
    FrequencyUnit,
    InductanceAttribute,
    InductanceUnit,
    PowerAttribute,
    PowerUnit,
    ResistanceAttribute,
    ResistanceUnit,
    StringAttribute,
    UnitlessUnit,
    VoltageAttribute,
    VoltageUnit,
)


@pytest.mark.parametrize(
    ['name', 'value', 'attribute_type', 'unit', 'output'],
    [
        (
            'n',
            'vvv',
            AttributeType.STRING,
            None,
            '(attribute "n" (type string) (unit none) (value "vvv"))',
        ),
        (
            'n',
            'vvv',
            AttributeType.STRING,
            UnitlessUnit.NONE,
            '(attribute "n" (type string) (unit none) (value "vvv"))',
        ),
        (
            'n',
            '0.1',
            AttributeType.CURRENT,
            CurrentUnit.MILLIAMPERE,
            '(attribute "n" (type current) (unit milliampere) (value "0.1"))',
        ),
        (
            'n',
            '0.1',
            AttributeType.CAPACITANCE,
            CapacitanceUnit.MILLIFARAD,
            '(attribute "n" (type capacitance) (unit millifarad) (value "0.1"))',
        ),
        (
            'n',
            '0.1',
            AttributeType.FREQUENCY,
            FrequencyUnit.KILOHERTZ,
            '(attribute "n" (type frequency) (unit kilohertz) (value "0.1"))',
        ),
        (
            'n',
            '0.1',
            AttributeType.INDUCTANCE,
            InductanceUnit.MICROHENRY,
            '(attribute "n" (type inductance) (unit microhenry) (value "0.1"))',
        ),
        (
            'n',
            '0.1',
            AttributeType.POWER,
            PowerUnit.WATT,
            '(attribute "n" (type power) (unit watt) (value "0.1"))',
        ),
        (
            'n',
            '0.1',
            AttributeType.RESISTANCE,
            ResistanceUnit.MEGAOHM,
            '(attribute "n" (type resistance) (unit megaohm) (value "0.1"))',
        ),
        (
            'n',
            '0.1',
            AttributeType.VOLTAGE,
            VoltageUnit.KILOVOLT,
            '(attribute "n" (type voltage) (unit kilovolt) (value "0.1"))',
        ),
        # add more for new types
    ],
)
def test_attribute(
    name: str, value: str, attribute_type: AttributeType, unit: Optional[AttributeUnit], output: str
) -> None:
    attribute_s_exp = str(Attribute(name, value, attribute_type, unit))
    assert attribute_s_exp == output


@pytest.mark.parametrize(
    ['attr', 'attribute_type'],
    [
        (StringAttribute('s', 'a'), AttributeType.STRING),
        (CurrentAttribute('c', '1', CurrentUnit.AMPERE), AttributeType.CURRENT),
        (CapacitanceAttribute('c', '1', CapacitanceUnit.FARAD), AttributeType.CAPACITANCE),
        (FrequencyAttribute('f', '1', FrequencyUnit.HERTZ), AttributeType.FREQUENCY),
        (InductanceAttribute('i', '1', InductanceUnit.HENRY), AttributeType.INDUCTANCE),
        (PowerAttribute('p', '1', PowerUnit.WATT), AttributeType.POWER),
        (ResistanceAttribute('r', '1', ResistanceUnit.OHM), AttributeType.RESISTANCE),
        (VoltageAttribute('v', '1', VoltageUnit.VOLT), AttributeType.VOLTAGE),
        # add more for new types
    ],
)
def test_typed_attribute_has_correct_type(attr: Attribute, attribute_type: AttributeType) -> None:
    assert attr.attribute_type == attribute_type


@pytest.mark.parametrize(
    'attr',
    [
        StringAttribute('s', 'a'),
        # add more for new unitless types
    ],
)
def test_unitless_typed_types_have_unit_none(attr: Attribute) -> None:
    assert attr.unit == UnitlessUnit.NONE


def test_none_unit_evaluates_to_unitless_none() -> None:
    # we pass None as unit
    a = Attribute('n', 'v', AttributeType.STRING, None)
    # check if it gets set to UnitlessUnit.NONE internally
    assert a.unit == UnitlessUnit.NONE


@pytest.mark.parametrize(
    ['typed', 'general'],
    [
        (StringAttribute('s', 'a'), Attribute('s', 'a', AttributeType.STRING, None)),
        (StringAttribute('s', 'a'), Attribute('s', 'a', AttributeType.STRING, UnitlessUnit.NONE)),
        (
            CurrentAttribute('c', '1', CurrentUnit.AMPERE),
            Attribute('c', '1', AttributeType.CURRENT, CurrentUnit.AMPERE),
        ),
        (
            CapacitanceAttribute('c', '1', CapacitanceUnit.FARAD),
            Attribute('c', '1', AttributeType.CAPACITANCE, CapacitanceUnit.FARAD),
        ),
        (
            FrequencyAttribute('f', '1', FrequencyUnit.HERTZ),
            Attribute('f', '1', AttributeType.FREQUENCY, FrequencyUnit.HERTZ),
        ),
        (
            InductanceAttribute('i', '1', InductanceUnit.HENRY),
            Attribute('i', '1', AttributeType.INDUCTANCE, InductanceUnit.HENRY),
        ),
        (
            PowerAttribute('p', '1', PowerUnit.WATT),
            Attribute('p', '1', AttributeType.POWER, PowerUnit.WATT),
        ),
        (
            ResistanceAttribute('r', '1', ResistanceUnit.OHM),
            Attribute('r', '1', AttributeType.RESISTANCE, ResistanceUnit.OHM),
        ),
        (
            VoltageAttribute('v', '1', VoltageUnit.VOLT),
            Attribute('v', '1', AttributeType.VOLTAGE, VoltageUnit.VOLT),
        ),
        # add more for new types
    ],
)
def test_typed_vs_general_attribute_equivalence(typed: Attribute, general: Attribute) -> None:
    assert str(typed) == str(general)
