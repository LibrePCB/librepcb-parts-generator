from entities.common import Name, Description, Position, Rotation, Length, Vertex, Angle, Polygon, Width, Fill, GrabArea, Layer, Align, Height, Text, Value, Keywords, Author, Version, Created, Category, Deprecated
from entities.symbol import Pin as SymbolPin, Symbol
from entities.component import Role, Signal, Required, Negated, Clock, ForcedNet, PinSignalMap, SignalUUID, TextDesignator, Gate, SymbolUUID, Suffix, Norm, Variant, Component, SchematicOnly, DefaultValue, Prefix


def test_name() -> None:
    name_s_exp = str(Name("bar"))
    assert name_s_exp == '(name "bar")'


def test_description() -> None:
    description = str(Description("My Description\\nWith two lines"))
    assert description == '(description "My Description\\nWith two lines")'


def test_position() -> None:
    pos_s_exp = str(Position(1.0, 2.0))
    assert pos_s_exp == '(position 1.0 2.0)'


def test_rotation() -> None:
    rotation_s_exp = str(Rotation(180.0))
    assert rotation_s_exp == '(rotation 180.0)'


def test_length() -> None:
    length_s_exp = str(Length(3.81))
    assert length_s_exp == '(length 3.81)'


def test_symbol_pin() -> None:
    symbol_pin_s_exp = str(SymbolPin('my_uuid', Name('foo'), Position(1.0, 2.0), Rotation(180.0), Length(3.81)))

    assert symbol_pin_s_exp == '(pin my_uuid (name "foo")\n' + \
        ' (position 1.0 2.0) (rotation 180.0) (length 3.81)\n' + \
        ')'


def test_vertex() -> None:
    vertex = str(Vertex(Position(-2.54, 22.86), Angle(0.0)))
    assert vertex == '(vertex (position -2.54 22.86) (angle 0.0))'


def test_polygon() -> None:
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


def test_text() -> None:
    text = str(Text('b9c4aa19-0a46-400c-9c96-e8c3dfb8f83e', Layer('sym_names'),
                    Value('{{NAME}}'), Align('center bottom'), Height(2.54),
                    Position(0.0, 22.86), Rotation(0.0)))
    assert text == '(text b9c4aa19-0a46-400c-9c96-e8c3dfb8f83e (layer sym_names) (value "{{NAME}}")\n' +\
        ' (align center bottom) (height 2.54) (position 0.0 22.86) (rotation 0.0)\n' +\
        ')'


def test_symbol() -> None:
    symbol = Symbol('01b03c10-7334-4bd5-b2bc-942c18325d2b', Name('Sym name'), Description(r'A multiline description.\n\nDescription'), Keywords('my, keywords'), Author('Test'), Version('0.2'), Created('2018-10-17T19:13:41Z'), Category('d0618c29-0436-42da-a388-fdadf7b23892'))
    symbol.add_pin(SymbolPin('6da06b2b-7806-4e68-bd0c-e9f18eb2f9d8', Name('1'), Position(5.08, 20.32), Rotation(180.0), Length(3.81)))
    polygon = Polygon('743dbf3d-98e8-46f0-9a32-00e00d0e811f', Layer('sym_outlines'), Width(0.25), Fill(False), GrabArea(True))
    polygon.add_vertex(Vertex(Position(-2.54, 22.86), Angle(0.0)))
    polygon.add_vertex(Vertex(Position(-2.54, -25.4), Angle(0.0)))
    polygon.add_vertex(Vertex(Position(-2.54, 22.86), Angle(0.0)))
    symbol.add_polygon(polygon)
    symbol.add_text(Text('b9c4aa19-0a46-400c-9c96-e8c3dfb8f83e', Layer('sym_names'), Value('{{NAME}}'), Align('center bottom'), Height(2.54), Position(0.0, 22.86), Rotation(0.0)))

    assert str(symbol) == """(librepcb_symbol 01b03c10-7334-4bd5-b2bc-942c18325d2b
 (name "Sym name")
 (description "A multiline description.\\n\\nDescription")
 (keywords "my, keywords")
 (author "Test")
 (version "0.2")
 (created 2018-10-17T19:13:41Z)
 (deprecated false)
 (category d0618c29-0436-42da-a388-fdadf7b23892)
 (pin 6da06b2b-7806-4e68-bd0c-e9f18eb2f9d8 (name "1")
  (position 5.08 20.32) (rotation 180.0) (length 3.81)
 )
 (polygon 743dbf3d-98e8-46f0-9a32-00e00d0e811f (layer sym_outlines)
  (width 0.25) (fill false) (grab_area true)
  (vertex (position -2.54 22.86) (angle 0.0))
  (vertex (position -2.54 -25.4) (angle 0.0))
  (vertex (position -2.54 22.86) (angle 0.0))
 )
 (text b9c4aa19-0a46-400c-9c96-e8c3dfb8f83e (layer sym_names) (value "{{NAME}}")
  (align center bottom) (height 2.54) (position 0.0 22.86) (rotation 0.0)
 )
)"""


def test_component_role() -> None:
    role = Role.PASSIVE
    assert role.value == 'passive'
    assert str(role) == '(role passive)'


def test_component_signal() -> None:
    signal = Signal('f46a4643-fc68-4593-a889-3d987bfe3544', Name('1'), Role.PASSIVE, Required(False), Negated(False), Clock(False), ForcedNet(''))
    assert str(signal) == """(signal f46a4643-fc68-4593-a889-3d987bfe3544 (name "1") (role passive)
 (required false) (negated false) (clock false) (forced_net "")
)"""


def test_component_pin_signal_map() -> None:
    pin_signal_map = PinSignalMap('0189aafc-f88a-4e65-8fb4-09a047a3e334', SignalUUID('46f7e0e2-74a6-442b-9a5c-1bd4ea3da59c'), TextDesignator.SYMBOL_PIN_NAME)

    assert str(pin_signal_map) == '(pin 0189aafc-f88a-4e65-8fb4-09a047a3e334 (signal 46f7e0e2-74a6-442b-9a5c-1bd4ea3da59c) (text pin))'


def test_component_gate() -> None:
    gate = Gate('c1e4b542-a1b1-44d5-bec3-070776143a29', SymbolUUID('8f1a97f2-4cdf-43da-b38d-b3787c47b5ad'), Position(0.0, 0.0), Rotation(0.0), Required(True), Suffix(''))
    gate.add_pin_signal_map(PinSignalMap('0189aafc-f88a-4e65-8fb4-09a047a3e334', SignalUUID('46f7e0e2-74a6-442b-9a5c-1bd4ea3da59c'), TextDesignator.SYMBOL_PIN_NAME))
    assert str(gate) == """(gate c1e4b542-a1b1-44d5-bec3-070776143a29
 (symbol 8f1a97f2-4cdf-43da-b38d-b3787c47b5ad)
 (position 0.0 0.0) (rotation 0.0) (required true) (suffix "")
 (pin 0189aafc-f88a-4e65-8fb4-09a047a3e334 (signal 46f7e0e2-74a6-442b-9a5c-1bd4ea3da59c) (text pin))
)"""


def test_component_variant() -> None:
    gate = Gate('c1e4b542-a1b1-44d5-bec3-070776143a29', SymbolUUID('8f1a97f2-4cdf-43da-b38d-b3787c47b5ad'), Position(0.0, 0.0), Rotation(0.0), Required(True), Suffix(''))
    gate.add_pin_signal_map(PinSignalMap('0189aafc-f88a-4e65-8fb4-09a047a3e334', SignalUUID('46f7e0e2-74a6-442b-9a5c-1bd4ea3da59c'), TextDesignator.SYMBOL_PIN_NAME))
    variant = Variant('abeeeed0-6e9a-4fdc-bc2b-e2c5b06bbe3a', Norm.EMPTY, Name('default'), Description(''), gate)
    assert str(variant) == """(variant abeeeed0-6e9a-4fdc-bc2b-e2c5b06bbe3a (norm "")
 (name "default")
 (description "")
 (gate c1e4b542-a1b1-44d5-bec3-070776143a29
  (symbol 8f1a97f2-4cdf-43da-b38d-b3787c47b5ad)
  (position 0.0 0.0) (rotation 0.0) (required true) (suffix "")
  (pin 0189aafc-f88a-4e65-8fb4-09a047a3e334 (signal 46f7e0e2-74a6-442b-9a5c-1bd4ea3da59c) (text pin))
 )
)"""


def test_component() -> None:
    component = Component('00c36da8-e22b-43a1-9a87-c3a67e863f49', Name('Generic Connector 1x27'), Description(r'A 1x27 soldered wire connector.\n\nNext line'), Keywords('connector, 1x27'), Author('Test R.'), Version('0.2'), Created('2018-10-17T19:13:41Z'), Deprecated(False), Category('d0618c29-0436-42da-a388-fdadf7b23892'), SchematicOnly(False), DefaultValue(''), Prefix('J'))
    component.add_signal(Signal('f46a4643-fc68-4593-a889-3d987bfe3544', Name('1'), Role.PASSIVE, Required(False), Negated(False), Clock(False), ForcedNet('')))

    gate = Gate('c1e4b542-a1b1-44d5-bec3-070776143a29', SymbolUUID('8f1a97f2-4cdf-43da-b38d-b3787c47b5ad'), Position(0.0, 0.0), Rotation(0.0), Required(True), Suffix(''))
    gate.add_pin_signal_map(PinSignalMap('0189aafc-f88a-4e65-8fb4-09a047a3e334', SignalUUID('46f7e0e2-74a6-442b-9a5c-1bd4ea3da59c'), TextDesignator.SYMBOL_PIN_NAME))
    variant = Variant('abeeeed0-6e9a-4fdc-bc2b-e2c5b06bbe3a', Norm.EMPTY, Name('default'), Description(''), gate)

    component.add_variant(variant)

    assert str(component) == """(librepcb_component 00c36da8-e22b-43a1-9a87-c3a67e863f49
 (name "Generic Connector 1x27")
 (description "A 1x27 soldered wire connector.\\n\\nNext line")
 (keywords "connector, 1x27")
 (author "Test R.")
 (version "0.2")
 (created 2018-10-17T19:13:41Z)
 (deprecated false)
 (category d0618c29-0436-42da-a388-fdadf7b23892)
 (schematic_only false)
 (default_value "")
 (prefix "J")
 (signal f46a4643-fc68-4593-a889-3d987bfe3544 (name "1") (role passive)
  (required false) (negated false) (clock false) (forced_net "")
 )
 (variant abeeeed0-6e9a-4fdc-bc2b-e2c5b06bbe3a (norm "")
  (name "default")
  (description "")
  (gate c1e4b542-a1b1-44d5-bec3-070776143a29
   (symbol 8f1a97f2-4cdf-43da-b38d-b3787c47b5ad)
   (position 0.0 0.0) (rotation 0.0) (required true) (suffix "")
   (pin 0189aafc-f88a-4e65-8fb4-09a047a3e334 (signal 46f7e0e2-74a6-442b-9a5c-1bd4ea3da59c) (text pin))
  )
 )
)"""
