from entities import Position, Rotation, Length, SchematicsPin


def test_position():
    pos_s_exp = Position(1.0, 2.0).to_s_exp()
    assert pos_s_exp == '(position 1.0 2.0)'


def test_rotation():
    rotation_s_exp = Rotation(180.0).to_s_exp()
    assert rotation_s_exp == '(rotation 180.0)'


def test_length():
    length_s_exp = Length(3.81).to_s_exp()
    assert length_s_exp == '(length 3.81)'


def test_schematics_pin():
    schematics_pin_s_exp = SchematicsPin('my_uuid', 'foo', Position(1.0, 2.0), Rotation(180.0), Length(3.81)).to_s_exp()
    assert schematics_pin_s_exp == [
        '(pin my_uuid (name "foo")',
        ' (position 1.0 2.0) (rotation 180.0) (length 3.81)',
        ')',
    ]
