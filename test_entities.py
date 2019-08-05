from entities.common import Name, Description, Position, Rotation, Length, Vertex, Angle, Polygon, Width, Fill, GrabArea, Layer, Align, Height, Text, Value
from entities.symbol import Pin as SymbolPin


def test_name():
    name_s_exp = str(Name("bar"))
    assert name_s_exp == '(name "bar")'


def test_description():
    description = str(Description("My Description\\nWith two lines"))
    assert description == '(description "My Description\\nWith two lines")'


def test_position():
    pos_s_exp = str(Position(1.0, 2.0))
    assert pos_s_exp == '(position 1.0 2.0)'


def test_rotation():
    rotation_s_exp = str(Rotation(180.0))
    assert rotation_s_exp == '(rotation 180.0)'


def test_length():
    length_s_exp = str(Length(3.81))
    assert length_s_exp == '(length 3.81)'


def test_symbol_pin():
    symbol_pin_s_exp = str(SymbolPin('my_uuid', Name('foo'), Position(1.0, 2.0), Rotation(180.0), Length(3.81)))

    assert symbol_pin_s_exp == '(pin my_uuid (name "foo")\n' + \
        ' (position 1.0 2.0) (rotation 180.0) (length 3.81)\n' + \
        ')'


def test_vertex():
    vertex = str(Vertex(Position(-2.54, 22.86), Angle(0.0)))
    assert vertex == '(vertex (position -2.54 22.86) (angle 0.0))'


def test_polygon():
    polygon = Polygon('743dbf3d-98e8-46f0-9a32-00e00d0e811f', Layer('sym_outlines'), Width(0.25), Fill(False), GrabArea(True))
    polygon.add_vertex(Vertex(Position(-2.54, 22.86), Angle(0.0)))
    polygon.add_vertex(Vertex(Position( 2.54, 22.86), Angle(0.0)))
    polygon.add_vertex(Vertex(Position( 2.54, -25.4), Angle(0.0)))
    polygon.add_vertex(Vertex(Position(-2.54, -25.4), Angle(0.0)))
    polygon.add_vertex(Vertex(Position(-2.54, 22.86), Angle(0.0)))

    assert str(polygon) == '(polygon 743dbf3d-98e8-46f0-9a32-00e00d0e811f (layer sym_outlines)\n' +\
        ' (width 0.25) (fill false) (grab_area true)\n' +\
        ' (vertex (position -2.54 22.86) (angle 0.0))\n' +\
        ' (vertex (position 2.54 22.86) (angle 0.0))\n' +\
        ' (vertex (position 2.54 -25.4) (angle 0.0))\n' +\
        ' (vertex (position -2.54 -25.4) (angle 0.0))\n' +\
        ' (vertex (position -2.54 22.86) (angle 0.0))\n' +\
        ')'


def test_text():
    text = str(Text('b9c4aa19-0a46-400c-9c96-e8c3dfb8f83e', Layer('sym_names'),
                    Value('{{NAME}}'), Align('center bottom'), Height(2.54),
                    Position(0.0, 22.86), Rotation(0.0)))
    assert text == '(text b9c4aa19-0a46-400c-9c96-e8c3dfb8f83e (layer sym_names) (value "{{NAME}}")\n' +\
        ' (align center bottom) (height 2.54) (position 0.0 22.86) (rotation 0.0)\n' +\
        ')'
