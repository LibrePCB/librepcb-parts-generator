import pytest

from common import escape_string, format_float, format_ipc_dimension, human_sort_key, sign


@pytest.mark.parametrize(['inval', 'outval'], [
    ('', ''),
    ('"', '\\"'),
    ('\n', '\\n'),
    ('\\', '\\\\'),
])
def test_escape_string(inval: str, outval: str) -> None:
    assert escape_string(inval) == outval


@pytest.mark.parametrize(['inval', 'outval'], [
    (3.14456, '3.145'),
    (-7.0, '-7.0'),
    (0.4, '0.4'),
    (-0.0, '0.0'),
    (-0.0001, '0.0'),  # Unsigned zero, due to rounding to 3 decimals
])
def test_format_float(inval: float, outval: str) -> None:
    assert format_float(inval) == outval


@pytest.mark.parametrize(['inval', 'decimals', 'outval'], [
    (3.14456, 1, '31'),
    (3.14456, 2, '314'),
    (75.0, 2, '7500'),
    (0.4, 2, '40'),
    (0.75, 2, '75'),
    (30.0, 2, '3000'),
    (0.7999999999, 2, '80'),
    (0.809, 2, '80'),
])
def test_format_ipc_dimension(inval: float, decimals: int, outval: str) -> None:
    assert format_ipc_dimension(inval, decimals) == outval


@pytest.mark.parametrize(['inval', 'outval'], [
    (3.14456, 1),
    (75.0, 1),
    (0, 1),
    (0.0, 1),
    (-0.0, 1),
    (-1, -1),
    (-0.001, -1),
])
def test_sign(inval: float, outval: int) -> None:
    assert sign(inval) == outval


@pytest.mark.parametrize(['inval', 'outval'], [
    ('123', [123]),
    ('PA10-PB1', ['PA', 10, '-PB', 1]),
])
def test_human_sort_key(inval, outval):
    assert human_sort_key(inval) == outval


@pytest.mark.parametrize(['inlist', 'sortedlist'], [
    (['PA5', 'PA10', 'PA4', 'PB12'], ['PA4', 'PA5', 'PA10', 'PB12']),
])
def test_human_sort_key_list(inlist, sortedlist):
    assert sorted(inlist, key=human_sort_key) == sortedlist
