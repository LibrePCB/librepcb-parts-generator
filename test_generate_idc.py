import pytest

import generate_idc


@pytest.mark.parametrize([
    'pin_number',
    'pin_count',
    'row_count',
    'pitch',
    'row_spacing',
    'x',
    'y',
], [
    # 2x4
    (1, 8, 2, 2.0, 3.0, -1.5, +3.0),
    (2, 8, 2, 2.0, 3.0, +1.5, +3.0),
    (3, 8, 2, 2.0, 3.0, -1.5, +1.0),
    (4, 8, 2, 2.0, 3.0, +1.5, +1.0),
    (5, 8, 2, 2.0, 3.0, -1.5, -1.0),
    (6, 8, 2, 2.0, 3.0, +1.5, -1.0),
    (7, 8, 2, 2.0, 3.0, -1.5, -3.0),
    (8, 8, 2, 2.0, 3.0, +1.5, -3.0),
])
def test_get_coords(pin_number, pin_count, row_count, pitch, row_spacing, x, y):
    coord = generate_idc.get_coords(pin_number, pin_count, row_count, pitch, row_spacing)
    assert coord.x == x
    assert coord.y == y
