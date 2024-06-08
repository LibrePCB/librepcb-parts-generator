from pathlib import Path

from entities.common import (
    Align, Angle, Author, Category, Circle, Created, Deprecated, Description, Diameter, Fill, GeneratedBy, GrabArea,
    Height, Keywords, Layer, Length, Name, Polygon, Position, Position3D, Rotation, Rotation3D, Text, Value, Version,
    Vertex, Width
)
from entities.component import (
    Clock, Component, DefaultValue, ForcedNet, Gate, Negated, Norm, PinSignalMap, Prefix, Required, Role, SchematicOnly,
    Signal, SignalUUID, Suffix, SymbolUUID, TextDesignator, Variant
)
from entities.device import ComponentPad, ComponentUUID, Device, Manufacturer, PackageUUID, Part
from entities.package import (
    AssemblyType, AutoRotate, ComponentSide, CopperClearance, DrillDiameter, Footprint, Footprint3DModel, FootprintPad,
    LetterSpacing, LineSpacing, Mirror, Package, Package3DModel, PackagePad, PackagePadUuid, PadFunction, PadHole,
    Shape, ShapeRadius, Size, SolderPasteConfig, StopMaskConfig, StrokeText, StrokeWidth
)
from entities.symbol import NameAlign, NameHeight, NamePosition, NameRotation
from entities.symbol import Pin as SymbolPin
from entities.symbol import Symbol


def test_name() -> None:
    name_s_exp = str(Name("bar"))
    assert name_s_exp == '(name "bar")'


def test_description() -> None:
    description = str(Description("My Description\nWith two \" lines"))
    assert description == '(description "My Description\\nWith two \\" lines")'


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
    symbol_pin_s_exp = str(SymbolPin(
        'my_uuid',
        Name('foo'),
        Position(1.0, 2.0),
        Rotation(180.0),
        Length(3.81),
        NamePosition(3.0, 4.0),
        NameRotation(270.0),
        NameHeight(2.5),
        NameAlign('left center'),
    ))

    assert symbol_pin_s_exp == '(pin my_uuid (name "foo")\n' + \
        ' (position 1.0 2.0) (rotation 180.0) (length 3.81)\n' + \
        ' (name_position 3.0 4.0) (name_rotation 270.0) (name_height 2.5)\n' + \
        ' (name_align left center)\n' + \
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
    symbol = Symbol(
        '01b03c10-7334-4bd5-b2bc-942c18325d2b',
        Name('Sym name'),
        Description('A multiline description.\n\nDescription'),
        Keywords('my, keywords'),
        Author('Test'),
        Version('0.2'),
        Created('2018-10-17T19:13:41Z'),
        Deprecated(False),
        GeneratedBy('black magic'),
        [Category('d0618c29-0436-42da-a388-fdadf7b23892')],
    )
    symbol.add_pin(SymbolPin(
        '6da06b2b-7806-4e68-bd0c-e9f18eb2f9d8',
        Name('1'),
        Position(5.08, 20.32),
        Rotation(180.0),
        Length(3.81),
        NamePosition(1.0, 2.0),
        NameRotation(270.0),
        NameHeight(2.5),
        NameAlign('left center'),
    ))
    polygon = Polygon('743dbf3d-98e8-46f0-9a32-00e00d0e811f', Layer('sym_outlines'), Width(0.25), Fill(False), GrabArea(True))
    polygon.add_vertex(Vertex(Position(-2.54, 22.86), Angle(0.0)))
    polygon.add_vertex(Vertex(Position(-2.54, -25.4), Angle(0.0)))
    polygon.add_vertex(Vertex(Position(-2.54, 22.86), Angle(0.0)))
    symbol.add_polygon(polygon)
    symbol.add_circle(Circle('b5599e68-ff6a-464b-9a40-c6ba8ef8daf5', Layer('sym_outlines'), Width(0.254), Fill(False), GrabArea(False), Diameter(1.27), Position(5.715, 0.0)))
    symbol.add_text(Text('b9c4aa19-0a46-400c-9c96-e8c3dfb8f83e', Layer('sym_names'), Value('{{NAME}}'), Align('center bottom'), Height(2.54), Position(0.0, 22.86), Rotation(0.0)))
    symbol.add_approval('(approval foo)')
    symbol.add_approval('(approval bar)')

    assert str(symbol) == """(librepcb_symbol 01b03c10-7334-4bd5-b2bc-942c18325d2b
 (name "Sym name")
 (description "A multiline description.\\n\\nDescription")
 (keywords "my, keywords")
 (author "Test")
 (version "0.2")
 (created 2018-10-17T19:13:41Z)
 (deprecated false)
 (generated_by "black magic")
 (category d0618c29-0436-42da-a388-fdadf7b23892)
 (pin 6da06b2b-7806-4e68-bd0c-e9f18eb2f9d8 (name "1")
  (position 5.08 20.32) (rotation 180.0) (length 3.81)
  (name_position 1.0 2.0) (name_rotation 270.0) (name_height 2.5)
  (name_align left center)
 )
 (polygon 743dbf3d-98e8-46f0-9a32-00e00d0e811f (layer sym_outlines)
  (width 0.25) (fill false) (grab_area true)
  (vertex (position -2.54 22.86) (angle 0.0))
  (vertex (position -2.54 -25.4) (angle 0.0))
  (vertex (position -2.54 22.86) (angle 0.0))
 )
 (circle b5599e68-ff6a-464b-9a40-c6ba8ef8daf5 (layer sym_outlines)
  (width 0.254) (fill false) (grab_area false) (diameter 1.27) (position 5.715 0.0)
 )
 (text b9c4aa19-0a46-400c-9c96-e8c3dfb8f83e (layer sym_names) (value "{{NAME}}")
  (align center bottom) (height 2.54) (position 0.0 22.86) (rotation 0.0)
 )
 (approval bar)
 (approval foo)
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
    component = Component(
        '00c36da8-e22b-43a1-9a87-c3a67e863f49',
        Name('Generic Connector 1x27'),
        Description('A 1x27 soldered wire connector.\n\nNext line'),
        Keywords('connector, 1x27'),
        Author('Test R.'),
        Version('0.2'),
        Created('2018-10-17T19:13:41Z'),
        Deprecated(False),
        GeneratedBy('black magic'),
        [Category('d0618c29-0436-42da-a388-fdadf7b23892')],
        SchematicOnly(False),
        DefaultValue(''),
        Prefix('J'),
    )
    component.add_signal(Signal('f46a4643-fc68-4593-a889-3d987bfe3544', Name('1'), Role.PASSIVE, Required(False), Negated(False), Clock(False), ForcedNet('')))

    gate = Gate('c1e4b542-a1b1-44d5-bec3-070776143a29', SymbolUUID('8f1a97f2-4cdf-43da-b38d-b3787c47b5ad'), Position(0.0, 0.0), Rotation(0.0), Required(True), Suffix(''))
    gate.add_pin_signal_map(PinSignalMap('0189aafc-f88a-4e65-8fb4-09a047a3e334', SignalUUID('46f7e0e2-74a6-442b-9a5c-1bd4ea3da59c'), TextDesignator.SYMBOL_PIN_NAME))
    variant = Variant('abeeeed0-6e9a-4fdc-bc2b-e2c5b06bbe3a', Norm.EMPTY, Name('default'), Description(''), gate)
    component.add_variant(variant)

    component.add_approval('(approval foo)')
    component.add_approval('(approval bar)')

    assert str(component) == """(librepcb_component 00c36da8-e22b-43a1-9a87-c3a67e863f49
 (name "Generic Connector 1x27")
 (description "A 1x27 soldered wire connector.\\n\\nNext line")
 (keywords "connector, 1x27")
 (author "Test R.")
 (version "0.2")
 (created 2018-10-17T19:13:41Z)
 (deprecated false)
 (generated_by "black magic")
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
 (approval bar)
 (approval foo)
)"""


def test_package_pad() -> None:
    package_pad = PackagePad('5c4d39d3-35cc-4836-a082-693143ee9135', Name('1'))
    assert str(package_pad) == '(pad 5c4d39d3-35cc-4836-a082-693143ee9135 (name "1"))'


def test_footprint_pad() -> None:
    footprint_pad = FootprintPad(
        '5c4d39d3-35cc-4836-a082-693143ee9135',
        ComponentSide.TOP,
        Shape.ROUNDED_RECT,
        Position(0.0, 22.86),
        Rotation(0.0),
        Size(2.54, 1.5875),
        ShapeRadius(0.5),
        StopMaskConfig.AUTO,
        SolderPasteConfig.OFF,
        CopperClearance(0.1),
        PadFunction.UNSPECIFIED,
        PackagePadUuid('5c4d39d3-35cc-4836-a082-693143ee9135'),
        [
            PadHole(
                '5c4d39d3-35cc-4836-a082-693143ee9135',
                DrillDiameter(1.0),
                [Vertex(Position(0.0, 0.0), Angle(0.0))]
            ),
        ],
    )
    assert str(footprint_pad) == """(pad 5c4d39d3-35cc-4836-a082-693143ee9135 (side top) (shape roundrect)
 (position 0.0 22.86) (rotation 0.0) (size 2.54 1.587) (radius 0.5)
 (stop_mask auto) (solder_paste off) (clearance 0.1) (function unspecified)
 (package_pad 5c4d39d3-35cc-4836-a082-693143ee9135)
 (hole 5c4d39d3-35cc-4836-a082-693143ee9135 (diameter 1.0)
  (vertex (position 0.0 0.0) (angle 0.0))
 )
)"""


def test_stroke_text() -> None:
    stroke_text = StrokeText('f16d1604-8a82-4688-bc58-be1c1375873f', Layer('top_names'), Height(1.0), StrokeWidth(0.2), LetterSpacing.AUTO, LineSpacing.AUTO, Align('center bottom'), Position(0.0, 25.63), Rotation(0.0), AutoRotate(True), Mirror(False), Value('{{NAME}}'))
    assert str(stroke_text) == """(stroke_text f16d1604-8a82-4688-bc58-be1c1375873f (layer top_names)
 (height 1.0) (stroke_width 0.2) (letter_spacing auto) (line_spacing auto)
 (align center bottom) (position 0.0 25.63) (rotation 0.0)
 (auto_rotate true) (mirror false) (value "{{NAME}}")
)"""


def create_footprint() -> Footprint:
    footprint = Footprint(
        '17b9f232-2b15-4281-a07d-ad0db5213f92',
        Name('default'),
        Description(''),
        Position3D(1.0, 2.0, 3.0),
        Rotation3D(10.0, 20.0, 30.0),
    )
    footprint.add_3d_model(Footprint3DModel('ea459880-68df-4929-b796-b5c8686a1862'))
    footprint.add_pad(FootprintPad(
        '5c4d39d3-35cc-4836-a082-693143ee9135',
        ComponentSide.TOP,
        Shape.ROUNDED_RECT,
        Position(0.0, 22.86),
        Rotation(0.0),
        Size(2.54, 1.5875),
        ShapeRadius(0.5),
        StopMaskConfig.AUTO,
        SolderPasteConfig.OFF,
        CopperClearance(0.1),
        PadFunction.UNSPECIFIED,
        PackagePadUuid('5c4d39d3-35cc-4836-a082-693143ee9135'),
        [
            PadHole(
                '5c4d39d3-35cc-4836-a082-693143ee9135',
                DrillDiameter(1.0),
                [Vertex(Position(0.0, 0.0), Angle(0.0))]
            ),
        ],
    ))
    footprint.add_pad(FootprintPad(
        '6100dd55-d3b3-4139-9085-d5a75e783c37',
        ComponentSide.TOP,
        Shape.ROUNDED_RECT,
        Position(0.0, 20.32),
        Rotation(0.0),
        Size(2.54, 1.5875),
        ShapeRadius(0.5),
        StopMaskConfig.AUTO,
        SolderPasteConfig.OFF,
        CopperClearance(0.1),
        PadFunction.UNSPECIFIED,
        PackagePadUuid('6100dd55-d3b3-4139-9085-d5a75e783c37'),
        [
            PadHole(
                '6100dd55-d3b3-4139-9085-d5a75e783c37',
                DrillDiameter(1.0),
                [Vertex(Position(0.0, 0.0), Angle(0.0))]
            ),
        ],
    ))
    polygon = Polygon('5e18e4ea-5667-42b3-b60f-fcc91b0461d3', Layer('top_placement'), Width(0.25), Fill(False), GrabArea(True))
    polygon.add_vertex(Vertex(Position(-1.27, +24.36), Angle(0.0)))
    polygon.add_vertex(Vertex(Position(+1.27, +24.36), Angle(0.0)))
    polygon.add_vertex(Vertex(Position(+1.27, -24.36), Angle(0.0)))
    polygon.add_vertex(Vertex(Position(-1.27, -24.36), Angle(0.0)))
    polygon.add_vertex(Vertex(Position(-1.27, +24.36), Angle(0.0)))
    footprint.add_polygon(polygon)
    stroke_text = StrokeText('f16d1604-8a82-4688-bc58-be1c1375873f', Layer('top_names'), Height(1.0), StrokeWidth(0.2), LetterSpacing.AUTO, LineSpacing.AUTO, Align('center bottom'), Position(0.0, 25.63), Rotation(0.0), AutoRotate(True), Mirror(False), Value('{{NAME}}'))
    footprint.add_text(stroke_text)
    return footprint


def test_footprint() -> None:
    footprint = create_footprint()
    assert str(footprint) == """(footprint 17b9f232-2b15-4281-a07d-ad0db5213f92
 (name "default")
 (description "")
 (3d_position 1.0 2.0 3.0) (3d_rotation 10.0 20.0 30.0)
 (3d_model ea459880-68df-4929-b796-b5c8686a1862)
 (pad 5c4d39d3-35cc-4836-a082-693143ee9135 (side top) (shape roundrect)
  (position 0.0 22.86) (rotation 0.0) (size 2.54 1.587) (radius 0.5)
  (stop_mask auto) (solder_paste off) (clearance 0.1) (function unspecified)
  (package_pad 5c4d39d3-35cc-4836-a082-693143ee9135)
  (hole 5c4d39d3-35cc-4836-a082-693143ee9135 (diameter 1.0)
   (vertex (position 0.0 0.0) (angle 0.0))
  )
 )
 (pad 6100dd55-d3b3-4139-9085-d5a75e783c37 (side top) (shape roundrect)
  (position 0.0 20.32) (rotation 0.0) (size 2.54 1.587) (radius 0.5)
  (stop_mask auto) (solder_paste off) (clearance 0.1) (function unspecified)
  (package_pad 6100dd55-d3b3-4139-9085-d5a75e783c37)
  (hole 6100dd55-d3b3-4139-9085-d5a75e783c37 (diameter 1.0)
   (vertex (position 0.0 0.0) (angle 0.0))
  )
 )
 (polygon 5e18e4ea-5667-42b3-b60f-fcc91b0461d3 (layer top_placement)
  (width 0.25) (fill false) (grab_area true)
  (vertex (position -1.27 24.36) (angle 0.0))
  (vertex (position 1.27 24.36) (angle 0.0))
  (vertex (position 1.27 -24.36) (angle 0.0))
  (vertex (position -1.27 -24.36) (angle 0.0))
  (vertex (position -1.27 24.36) (angle 0.0))
 )
 (stroke_text f16d1604-8a82-4688-bc58-be1c1375873f (layer top_names)
  (height 1.0) (stroke_width 0.2) (letter_spacing auto) (line_spacing auto)
  (align center bottom) (position 0.0 25.63) (rotation 0.0)
  (auto_rotate true) (mirror false) (value "{{NAME}}")
 )
)"""


def test_package() -> None:
    package = Package(
        '009e35ef-1f50-4bf3-ab58-11eb85bf5503',
        Name('Soldered Wire Connector 1x19 ⌀1.0mm'),
        Description('A 1x19 soldered wire connector with 2.54mm pin spacing and 1.0mm drill holes.\n\nGenerated with librepcb-parts-generator (generate_connectors.py)'),
        Keywords('connector, 1x19, d1.0, connector, soldering, generic'),
        Author('Danilo B.'),
        Version('0.1'),
        Created('2018-10-17T19:13:41Z'),
        Deprecated(False),
        GeneratedBy('black magic'),
        [Category('56a5773f-eeb4-4b39-8cb9-274f3da26f4f')],
        AssemblyType.THT,
    )

    package.add_pad(PackagePad('5c4d39d3-35cc-4836-a082-693143ee9135', Name('1')))
    package.add_pad(PackagePad('6100dd55-d3b3-4139-9085-d5a75e783c37', Name('2')))

    package.add_3d_model(Package3DModel('ea459880-68df-4929-b796-b5c8686a1862', Name('3dmodel')))

    package.add_footprint(create_footprint())

    package.add_approval('(approval foo)')
    package.add_approval('(approval bar)')

    assert str(package) == """(librepcb_package 009e35ef-1f50-4bf3-ab58-11eb85bf5503
 (name "Soldered Wire Connector 1x19 ⌀1.0mm")
 (description "A 1x19 soldered wire connector with 2.54mm pin spacing and 1.0mm drill holes.\\n\\nGenerated with librepcb-parts-generator (generate_connectors.py)")
 (keywords "connector, 1x19, d1.0, connector, soldering, generic")
 (author "Danilo B.")
 (version "0.1")
 (created 2018-10-17T19:13:41Z)
 (deprecated false)
 (generated_by "black magic")
 (category 56a5773f-eeb4-4b39-8cb9-274f3da26f4f)
 (assembly_type tht)
 (pad 5c4d39d3-35cc-4836-a082-693143ee9135 (name "1"))
 (pad 6100dd55-d3b3-4139-9085-d5a75e783c37 (name "2"))
 (3d_model ea459880-68df-4929-b796-b5c8686a1862 (name "3dmodel"))
 (footprint 17b9f232-2b15-4281-a07d-ad0db5213f92
  (name "default")
  (description "")
  (3d_position 1.0 2.0 3.0) (3d_rotation 10.0 20.0 30.0)
  (3d_model ea459880-68df-4929-b796-b5c8686a1862)
  (pad 5c4d39d3-35cc-4836-a082-693143ee9135 (side top) (shape roundrect)
   (position 0.0 22.86) (rotation 0.0) (size 2.54 1.587) (radius 0.5)
   (stop_mask auto) (solder_paste off) (clearance 0.1) (function unspecified)
   (package_pad 5c4d39d3-35cc-4836-a082-693143ee9135)
   (hole 5c4d39d3-35cc-4836-a082-693143ee9135 (diameter 1.0)
    (vertex (position 0.0 0.0) (angle 0.0))
   )
  )
  (pad 6100dd55-d3b3-4139-9085-d5a75e783c37 (side top) (shape roundrect)
   (position 0.0 20.32) (rotation 0.0) (size 2.54 1.587) (radius 0.5)
   (stop_mask auto) (solder_paste off) (clearance 0.1) (function unspecified)
   (package_pad 6100dd55-d3b3-4139-9085-d5a75e783c37)
   (hole 6100dd55-d3b3-4139-9085-d5a75e783c37 (diameter 1.0)
    (vertex (position 0.0 0.0) (angle 0.0))
   )
  )
  (polygon 5e18e4ea-5667-42b3-b60f-fcc91b0461d3 (layer top_placement)
   (width 0.25) (fill false) (grab_area true)
   (vertex (position -1.27 24.36) (angle 0.0))
   (vertex (position 1.27 24.36) (angle 0.0))
   (vertex (position 1.27 -24.36) (angle 0.0))
   (vertex (position -1.27 -24.36) (angle 0.0))
   (vertex (position -1.27 24.36) (angle 0.0))
  )
  (stroke_text f16d1604-8a82-4688-bc58-be1c1375873f (layer top_names)
   (height 1.0) (stroke_width 0.2) (letter_spacing auto) (line_spacing auto)
   (align center bottom) (position 0.0 25.63) (rotation 0.0)
   (auto_rotate true) (mirror false) (value "{{NAME}}")
  )
 )
 (approval bar)
 (approval foo)
)"""


def test_component_pad() -> None:
    component_pad = ComponentPad('67a7b034-b30b-4644-b8d3-d7a99606efdc', SignalUUID('9bccea5e-e23f-4b88-9de1-4be00dc0c12a'))
    assert str(component_pad) == '(pad 67a7b034-b30b-4644-b8d3-d7a99606efdc (signal 9bccea5e-e23f-4b88-9de1-4be00dc0c12a))'


def test_device() -> None:
    device = Device(
        '00652f30-9f89-4027-91f5-7bd684eee751',
        Name('Foo'),
        Description('Bar'),
        Keywords('foo, bar'),
        Author('J. Rando'),
        Version('0.1'),
        Created('2018-10-17T19:13:41Z'),
        Deprecated(False),
        GeneratedBy('black magic'),
        [Category('ade6d8ff-3c4f-4dac-a939-cc540c87c280')],
        ComponentUUID('bc911fcc-8b5c-4728-b596-d644797c55da'),
        PackageUUID('b4e92c64-18c4-44a6-aa39-d1be3e8c29bd'),
    )
    device.add_pad(ComponentPad('aec3f475-28c4-4508-ab4f-e1b618a0d77d', SignalUUID('726fd1ce-a01b-4287-bb61-e3ff165a0644')))
    device.add_pad(ComponentPad('67a7b034-b30b-4644-b8d3-d7a99606efdc', SignalUUID('9bccea5e-e23f-4b88-9de1-4be00dc0c12a')))

    device.add_part(Part(mpn='mpn1', manufacturer=Manufacturer('man1')))
    device.add_part(Part(mpn='mpn2', manufacturer=Manufacturer('man2')))

    device.add_approval('(approval foo)')
    device.add_approval('(approval bar)')

    assert str(device) == """(librepcb_device 00652f30-9f89-4027-91f5-7bd684eee751
 (name "Foo")
 (description "Bar")
 (keywords "foo, bar")
 (author "J. Rando")
 (version "0.1")
 (created 2018-10-17T19:13:41Z)
 (deprecated false)
 (generated_by "black magic")
 (category ade6d8ff-3c4f-4dac-a939-cc540c87c280)
 (component bc911fcc-8b5c-4728-b596-d644797c55da)
 (package b4e92c64-18c4-44a6-aa39-d1be3e8c29bd)
 (pad 67a7b034-b30b-4644-b8d3-d7a99606efdc (signal 9bccea5e-e23f-4b88-9de1-4be00dc0c12a))
 (pad aec3f475-28c4-4508-ab4f-e1b618a0d77d (signal 726fd1ce-a01b-4287-bb61-e3ff165a0644))
 (part "mpn1" (manufacturer "man1")
 )
 (part "mpn2" (manufacturer "man2")
 )
 (approval bar)
 (approval foo)
)"""


def test_sort_package_3d_models() -> None:
    model1 = Package3DModel('2e2263b8-c5e2-4d09-87b2-5aafbfa836c9', Name('a'))
    model2 = Package3DModel('161c65b0-a386-4b45-9ac2-0293a812fb62', Name('b'))
    models = [model1, model2]
    assert sorted(models) == [model2, model1]


def test_sort_footprint_3d_models() -> None:
    model1 = Footprint3DModel('2e2263b8-c5e2-4d09-87b2-5aafbfa836c9')
    model2 = Footprint3DModel('161c65b0-a386-4b45-9ac2-0293a812fb62')
    models = [model1, model2]
    assert sorted(models) == [model2, model1]


def check_all_file_newlines_in_dir_are_unix(dir_with_files: Path) -> bool:
    """
    Checks if all files in the given directory have Unix-style line endings

    Helper function, not a test!
    """
    for temp_file in dir_with_files.iterdir():
        with temp_file.open(mode="r", newline='') as file_under_test:
            file_under_test.readlines()  # read all lines to populate file_under_test.newlines
            if file_under_test.newlines is None:
                return False
            if not all((newline == '\n') for newline in file_under_test.newlines):
                return False
    return True


def test_serialized_component_line_endings(tmp_path: Path) -> None:

    component_uuid = '00c36da8-e22b-43a1-9a87-c3a67e863f49'

    component = Component(
        component_uuid,
        Name('Generic Connector 1x27'),
        Description('A 1x27 soldered wire connector.\n\nNext line'),
        Keywords('connector, 1x27'),
        Author('Test R.'),
        Version('0.2'),
        Created('2018-10-17T19:13:41Z'),
        Deprecated(False),
        GeneratedBy('black magic'),
        [Category('d0618c29-0436-42da-a388-fdadf7b23892')],
        SchematicOnly(False),
        DefaultValue(''),
        Prefix('J'),
    )

    component.serialize(str(tmp_path))

    assert check_all_file_newlines_in_dir_are_unix(tmp_path.joinpath(component_uuid))


def test_serialized_symbol_line_endings(tmp_path: Path) -> None:

    symbol_uuid = '01b03c10-7334-4bd5-b2bc-942c18325d2b'

    symbol = Symbol(
        symbol_uuid,
        Name('Sym name'),
        Description('A multiline description.\n\nDescription'),
        Keywords('my, keywords'),
        Author('Test'),
        Version('0.2'),
        Created('2018-10-17T19:13:41Z'),
        Deprecated(False),
        GeneratedBy('black magic'),
        [Category('d0618c29-0436-42da-a388-fdadf7b23892')],
    )

    symbol.serialize(str(tmp_path))

    assert check_all_file_newlines_in_dir_are_unix(tmp_path.joinpath(symbol_uuid))


def test_serialized_device_line_endings(tmp_path: Path) -> None:

    device_uuid = '00652f30-9f89-4027-91f5-7bd684eee751'

    device = Device(
        device_uuid,
        Name('Foo'),
        Description('Bar'),
        Keywords('foo, bar'),
        Author('J. Rando'),
        Version('0.1'),
        Created('2018-10-17T19:13:41Z'),
        Deprecated(False),
        GeneratedBy('black magic'),
        [Category('ade6d8ff-3c4f-4dac-a939-cc540c87c280')],
        ComponentUUID('bc911fcc-8b5c-4728-b596-d644797c55da'),
        PackageUUID('b4e92c64-18c4-44a6-aa39-d1be3e8c29bd'),
    )

    device.serialize(str(tmp_path))

    assert check_all_file_newlines_in_dir_are_unix(tmp_path.joinpath(device_uuid))


def test_serialized_package_line_endings(tmp_path: Path) -> None:

    package_uuid = '009e35ef-1f50-4bf3-ab58-11eb85bf5503'

    package = Package(
        package_uuid,
        Name('Soldered Wire Connector 1x19 1.0mm'),
        Description('A 1x19 soldered wire connector with 2.54mm pin spacing and 1.0mm drill holes.\n\nGenerated with librepcb-parts-generator (generate_connectors.py)'),
        Keywords('connector, 1x19, d1.0, connector, soldering, generic'),
        Author('Danilo B.'),
        Version('0.1'),
        Created('2018-10-17T19:13:41Z'),
        Deprecated(False),
        GeneratedBy('black magic'),
        [Category('56a5773f-eeb4-4b39-8cb9-274f3da26f4f')],
        AssemblyType.THT,
    )

    package.serialize(str(tmp_path))

    assert check_all_file_newlines_in_dir_are_unix(tmp_path.joinpath(package_uuid))
