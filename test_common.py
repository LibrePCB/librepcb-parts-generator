import pytest

from common import format_float as ff, format_ipc_dimension


@pytest.mark.parametrize(['inval', 'outval'], [
    (3.14456, '3.145'),
    (-7.0, '-7.0'),
    (0.4, '0.4'),
    (-0.0, '0.0'),
])
def test_format_float(inval: float, outval: str):
    assert ff(inval) == outval


@pytest.mark.parametrize(['inval', 'outval'], [
    (3.14456, '314'),
    (75.0, '7500'),
    (0.4, '40'),
    (0.75, '75'),
])
def test_format_ipc_dimension(inval: float, outval: str):
    assert format_ipc_dimension(inval) == outval
