import pytest

from common import escape_string, format_float, format_ipc_dimension, human_sort_key, sign


@pytest.mark.parametrize(['inval', 'outval'], [
    ('', ''),
    ('"', '\\"'),
    ('\n', '\\n'),
    ('\\', '\\\\'),
])
def test_escape_string(inval: str, outval: str):
    assert escape_string(inval) == outval


@pytest.mark.parametrize(['inval', 'outval'], [
    (3.14456, '3.145'),
    (-7.0, '-7.0'),
    (0.4, '0.4'),
    (-0.0, '0.0'),
    (-0.0001, '0.0'),  # Unsigned zero, due to rounding to 3 decimals
])
def test_format_float(inval: float, outval: str):
    assert format_float(inval) == outval


@pytest.mark.parametrize(['inval', 'outval'], [
    (3.14456, '314'),
    (75.0, '7500'),
    (0.4, '40'),
    (0.75, '75'),
    (30.0, '3000'),
])
def test_format_ipc_dimension(inval: float, outval: str):
    assert format_ipc_dimension(inval) == outval


@pytest.mark.parametrize(['inval', 'outval'], [
    (3.14456, 1),
    (75.0, 1),
    (0, 1),
    (0.0, 1),
    (-0.0, 1),
    (-1, -1),
    (-0.001, -1),
])
def test_sign(inval: float, outval: str):
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
