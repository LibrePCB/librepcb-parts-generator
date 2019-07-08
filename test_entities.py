from entities import Position, Rotation, Length, SchematicsPin


def test_position():
    pos_s_exp = str(Position(1.0, 2.0))
    assert pos_s_exp == '(position 1.0 2.0)'


def test_rotation():
    rotation_s_exp = str(Rotation(180.0))
    assert rotation_s_exp == '(rotation 180.0)'


def test_length():
    length_s_exp = str(Length(3.81))
    assert length_s_exp == '(length 3.81)'


def test_schematics_pin():
    schematics_pin_s_exp = str(SchematicsPin('my_uuid', 'foo', Position(1.0, 2.0), Rotation(180.0), Length(3.81)))
    assert schematics_pin_s_exp == '(pin my_uuid (name "foo")\n' + \
        ' (position 1.0 2.0) (rotation 180.0) (length 3.81)\n' + \
        ')'
