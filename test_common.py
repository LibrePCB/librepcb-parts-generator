import pytest

from common import format_float as ff


@pytest.mark.parametrize(['inval', 'outval'], [
    (3.14456, '3.145'),
    (-7.0, '-7.0'),
    (0.4, '0.4'),
    (-0.0, '0.0'),
])
def test_format_float(inval: float, outval: str):
    assert ff(inval) == outval
