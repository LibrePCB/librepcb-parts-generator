import pytest

import generate_connectors


@pytest.mark.parametrize(['pin_number', 'pin_count', 'spacing', 'y'], [
    # Special case: 1
    (1, 1, 2.54, 0),

    # Odd number of pins
    (1, 5, 2.54, 5.08),
    (2, 5, 2.54, 2.54),
    (3, 5, 2.54, 0),
    (4, 5, 2.54, -2.54),
    (5, 5, 2.54, -5.08),

    # Even number of pins
    (1, 4, 1.6, 2.4),
    (2, 4, 1.6, 0.8),
    (3, 4, 1.6, -0.8),
    (4, 4, 1.6, -2.4),
])
def test_get_y(pin_number, pin_count, spacing, y):
    result = generate_connectors.get_y(pin_number, pin_count, spacing)
    assert result == y


@pytest.mark.parametrize(['pin_count', 'spacing', 'top', 'height'], [
    # Special case: 1
    (1, 1.6, 2, 2),

    # Odd number of pins
    (5, 2.54, 1.5, 5.08 + 1.5),

    # Even number of pins
    (6, 2.54, 1.5, 5.08 + 1.27 + 1.5),
])
def test_get_rectangle_height(pin_count, spacing, top, height):
    result = generate_connectors.get_rectangle_height(pin_count, spacing, top)
    assert result == height
