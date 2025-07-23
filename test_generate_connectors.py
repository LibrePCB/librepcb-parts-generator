import pytest

import generate_connectors


@pytest.mark.parametrize(
    ['pin_number', 'pin_count', 'rows', 'spacing', 'y'],
    [
        # Special case: 1
        (1, 1, 1, 2.54, 0),
        # Odd number of pins
        (1, 5, 1, 2.54, 5.08),
        (2, 5, 1, 2.54, 2.54),
        (3, 5, 1, 2.54, 0),
        (4, 5, 1, 2.54, -2.54),
        (5, 5, 1, 2.54, -5.08),
        # Even number of pins, grid align
        (1, 4, 1, 1.6, 1.6),
        (2, 4, 1, 1.6, 0),
        (3, 4, 1, 1.6, -1.6),
        (4, 4, 1, 1.6, -3.2),
        # Two rows, odd number of cols
        (1, 6, 2, 5.0, 5.0),
        (2, 6, 2, 5.0, 5.0),
        (3, 6, 2, 5.0, 0),
        (4, 6, 2, 5.0, 0),
        (5, 6, 2, 5.0, -5.0),
        (6, 6, 2, 5.0, -5.0),
        # Two rows, even number of cols, grid align
        (1, 4, 2, 1.0, 0.0),
        (2, 4, 2, 1.0, 0.0),
        (3, 4, 2, 1.0, -1.0),
        (4, 4, 2, 1.0, -1.0),
    ],
)
def test_get_y_grid_align(pin_number, pin_count, rows, spacing, y):
    result = generate_connectors.get_y(pin_number, pin_count, rows, spacing, True)
    assert result == y


@pytest.mark.parametrize(
    ['pin_count', 'rows', 'spacing', 'top', 'grid', 'expected'],
    [
        # Special case: 1
        (1, 1, 1.6, 2, True, (2, -2)),
        # Odd number of pins
        (5, 1, 2.54, 1.5, True, (5.08 + 1.5, -5.08 - 1.5)),
        # Even number of pins
        (6, 1, 2.54, 1.5, True, (2.54 * 2 + 1.5, -(2.54 * 3) - 1.5)),
        # Two rows, odd number of cols
        (6, 2, 1.0, 0.3, True, (1.3, -1.3)),
    ],
)
def test_get_rectangle_bounds(pin_count, rows, spacing, top, grid, expected):
    result = generate_connectors.get_rectangle_bounds(pin_count, rows, spacing, top, grid)
    assert result == pytest.approx(expected)
