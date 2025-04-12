"""
Generate pin header and socket packages.

             +---+- width
             v   v
             +---+ <-+
             |   |   | top
          +->| O | <!-- <-+
  spacing |  |(…)|
          +-> -->| O |
             |   |
             +---+

"""
import math
import sys
from functools import partial
from os import makedirs, path
from uuid import uuid4

from typing import Callable, Iterable, Optional, Tuple

from common import init_cache, now, save_cache
from entities.common import (
    Align, Angle, Author, Category, Circle, Created, Deprecated, Description, Diameter, Fill, GeneratedBy, GrabArea,
    Height, Keywords, Layer, Length, Name, Polygon, Position, Position3D, Rotation, Rotation3D, Text, Value, Version,
    Vertex, Width
)
from entities.component import (
    Clock, Component, DefaultValue, ForcedNet, Gate, Negated, Norm, PinSignalMap, Prefix, Required, Role, SchematicOnly,
    Signal, SignalUUID, Suffix, SymbolUUID, TextDesignator, Variant
)
from entities.package import (
    AssemblyType, AutoRotate, ComponentSide, CopperClearance, DrillDiameter, Footprint, Footprint3DModel, FootprintPad,
    LetterSpacing, LineSpacing, Mirror, Package, Package3DModel, PackagePad, PackagePadUuid, PadFunction, PadHole,
    Shape, ShapeRadius, Size, SolderPasteConfig, StopMaskConfig, StrokeText, StrokeWidth
)
from entities.symbol import NameAlign, NameHeight, NamePosition, NameRotation
from entities.symbol import Pin as SymbolPin
from entities.symbol import Symbol

generator = 'librepcb-parts-generator (generate_connectors.py)'

width = 2.54
spacing = 2.54
pad_size = (2.54 - 0.35, 1.27 * 1.25)
line_width = 0.25
pkg_text_height = 1.0
sym_text_height = 2.54
courtyard_offset = 0.5  # Rather large because packages are generic (i.e. not exact)


KIND_HEADER = 'pinheader'
KIND_SOCKET = 'pinsocket'
KIND_WIRE_CONNECTOR = 'wireconnector'
KIND_SCREW_TERMINAL = 'screwterminal'


# Initialize UUID cache
uuid_cache_file = 'uuid_cache_connectors.csv'
uuid_cache = init_cache(uuid_cache_file)


def uuid(category: str, kind: str, variant: str, identifier: str) -> str:
    """
    Return a uuid for the specified pin.

    Params:
        category:
            For example 'cmp' or 'pkg'.
        kind:
            For example 'pinheader' or 'pinsocket'.
        variant:
            For example '1x5-D1.1' or '1x13'.
        identifier:
            For example 'pad-1' or 'pin-13'.
    """
    key = '{}-{}-{}-{}'.format(category, kind, variant, identifier).lower().replace(' ', '~')
    if key not in uuid_cache:
        uuid_cache[key] = str(uuid4())
    return uuid_cache[key]


def get_y(pin_number: int, pin_count: int, rows: int, spacing: float, grid_align: bool) -> float:
    """
    Return the y coordinate of the specified pin. Keep the pins grid aligned, if desired.

    The pin number is 1 index based. Pin 1 is at the top. The middle pin will
    be at or near y=0.

    """
    # For two-row shapes, we map the values to the single-row variant
    pn = (pin_number + (rows - 1)) // rows
    pc = pin_count // rows

    # Calculate y
    if grid_align:
        mid = float((pc + 1) // 2)
    else:
        mid = (pc + 1) / 2
    y = -round(pn * spacing - mid * spacing, 2)
    if y == -0.0:  # Returns true for 0.0 too, but that doesn't matter
        return 0.0
    return y


def get_rectangle_bounds(
    pin_count: int,
    rows: int,
    spacing: float,
    top_offset: float,
    grid_align: bool,
) -> Tuple[float, float]:
    """
    Return (y_max/y_min) of the rectangle around the pins.
    """
    pc = pin_count // rows
    if grid_align:
        even = pc % 2 == 0
        offset = spacing / 2 if even else 0.0
    else:
        offset = 0.0
    height = (pc - 1) / 2 * spacing + top_offset
    return (height - offset, -height - offset)


def generate_pkg(
    library: str,
    author: str,
    name: str,
    name_lower: str,
    kind: str,
    assembly_type: AssemblyType,
    pkgcat: str,
    keywords: str,
    rows: int,
    min_pads: int,
    max_pads: int,
    pad_drills: Iterable[float],
    generate_silkscreen: Callable[[str, str, str, int, int], Polygon],
    generate_3d_model: Optional[Callable[[str, str, str, str, int, int, float], None]],
    generate_3d_models: bool,
    version: str,
    create_date: Optional[str],
) -> None:
    category = 'pkg'
    assert rows in [1, 2]
    for i in range(min_pads, max_pads + 1, rows):
        for drill in pad_drills:
            per_row = i // rows
            top_offset = spacing / 2

            variant = f'{rows}x{per_row}-D{drill:.1f}'

            def _uuid(identifier: str) -> str:
                return uuid(category, kind, variant, identifier)

            uuid_pkg = _uuid('pkg')
            uuid_pads = [_uuid('pad-{}'.format(p)) for p in range(i)]
            uuid_footprint = _uuid('footprint-default')
            uuid_outline = _uuid('polygon-outline')
            uuid_courtyard = _uuid('polygon-courtyard')
            uuid_text_name = _uuid('text-name')
            uuid_text_value = _uuid('text-value')

            full_name = f'{name} {rows}x{per_row:02d} ⌀{drill:.1f}mm'
            full_description = f'A generic {rows}x{per_row} {name_lower} ' + \
                               f'with {spacing}mm pin spacing and {drill:.1f}mm drill holes.' \
                               f'\n\nGenerated with {generator}'

            # Define package
            package = Package(
                uuid=uuid_pkg,
                name=Name(full_name),
                description=Description(full_description),
                keywords=Keywords(f'connector, {rows}x{per_row}, d{drill:.1f}, {keywords}'),
                author=Author(author),
                version=Version(version),
                created=Created(create_date or now()),
                deprecated=Deprecated(False),
                generated_by=GeneratedBy(''),
                categories=[Category(pkgcat)],
                assembly_type=assembly_type,
            )

            # Add pads to package
            for j in range(1, i + 1):
                package.add_pad(PackagePad(uuid_pads[j - 1], Name(str(j))))

            # Add footprint
            footprint = Footprint(
                uuid=uuid_footprint,
                name=Name('default'),
                description=Description(''),
                position_3d=Position3D.zero(),
                rotation_3d=Rotation3D.zero(),
            )
            package.add_footprint(footprint)

            # Add pads to footprint
            for p in range(1, i + 1):
                pad_uuid = uuid_pads[p - 1]
                if rows == 1:
                    x = 0.0
                elif rows == 2:
                    x = spacing / 2 if (p % rows == 0) else -spacing / 2
                y = get_y(p, i, rows, spacing, False)
                corner_radius = 0.0 if p == 1 else 1.0
                footprint.add_pad(FootprintPad(
                    uuid=pad_uuid,
                    side=ComponentSide.TOP,
                    shape=Shape.ROUNDED_RECT,
                    position=Position(x, y),
                    rotation=Rotation(0),
                    size=Size(pad_size[0], pad_size[1]),
                    radius=ShapeRadius(corner_radius),
                    stop_mask=StopMaskConfig(StopMaskConfig.AUTO),
                    solder_paste=SolderPasteConfig.OFF,
                    copper_clearance=CopperClearance(0.0),
                    function=PadFunction.STANDARD_PAD,
                    package_pad=PackagePadUuid(pad_uuid),
                    holes=[
                        PadHole(
                            pad_uuid,
                            DrillDiameter(drill),
                            [Vertex(Position(0.0, 0.0), Angle(0.0))],
                        )
                    ],
                ))

            # Add silkscreen to footprint
            silkscreen = generate_silkscreen(category, kind, variant, i, rows)
            footprint.add_polygon(silkscreen)

            # Package outline
            dx = (width + (rows - 1) * spacing) / 2
            dy = (width + (per_row - 1) * spacing) / 2
            footprint.add_polygon(Polygon(
                uuid=uuid_outline,
                layer=Layer('top_package_outlines'),
                width=Width(0),
                fill=Fill(False),
                grab_area=GrabArea(False),
                vertices=[
                    Vertex(Position(-dx, dy), Angle(0)),
                    Vertex(Position(dx, dy), Angle(0)),
                    Vertex(Position(dx, -dy), Angle(0)),
                    Vertex(Position(-dx, -dy), Angle(0)),
                ],
            ))

            # Courtyard
            dx += courtyard_offset
            dy += courtyard_offset
            footprint.add_polygon(Polygon(
                uuid=uuid_courtyard,
                layer=Layer('top_courtyard'),
                width=Width(0),
                fill=Fill(False),
                grab_area=GrabArea(False),
                vertices=[
                    Vertex(Position(-dx, dy), Angle(0)),
                    Vertex(Position(dx, dy), Angle(0)),
                    Vertex(Position(dx, -dy), Angle(0)),
                    Vertex(Position(-dx, -dy), Angle(0)),
                ],
            ))

            # Labels
            y_max, y_min = get_rectangle_bounds(i, rows, spacing, top_offset + 1.27, False)
            footprint.add_text(StrokeText(
                uuid=uuid_text_name,
                layer=Layer('top_names'),
                height=Height(pkg_text_height),
                stroke_width=StrokeWidth(0.2),
                letter_spacing=LetterSpacing.AUTO,
                line_spacing=LineSpacing.AUTO,
                align=Align('center bottom'),
                position=Position(0.0, y_max),
                rotation=Rotation(0.0),
                auto_rotate=AutoRotate(True),
                mirror=Mirror(False),
                value=Value('{{NAME}}'),
            ))
            footprint.add_text(StrokeText(
                uuid=uuid_text_value,
                layer=Layer('top_values'),
                height=Height(pkg_text_height),
                stroke_width=StrokeWidth(0.2),
                letter_spacing=LetterSpacing.AUTO,
                line_spacing=LineSpacing.AUTO,
                align=Align('center top'),
                position=Position(0.0, y_min),
                rotation=Rotation(0.0),
                auto_rotate=AutoRotate(True),
                mirror=Mirror(False),
                value=Value('{{VALUE}}'),
            ))

            # Generate 3D models (for some packages)
            if generate_3d_model is not None:
                uuid_3d = _uuid('3d')
                if generate_3d_models:
                    generate_3d_model(library, full_name, uuid_pkg, uuid_3d, rows, i, drill)
                package.add_3d_model(Package3DModel(uuid_3d, Name(full_name)))
                for footprint in package.footprints:
                    footprint.add_3d_model(Footprint3DModel(uuid_3d))

            # Message approvals
            if assembly_type == AssemblyType.NONE:
                # Assembly type is reported as suspicious because there are
                # some pads, but this is intended for soldered wire connectors.
                package.add_approval("(approved suspicious_assembly_type)")

            package.serialize(path.join('out', library, category))

            print('{}x{:02d} {} ⌀{:.1f}mm: Wrote package {}'.format(rows, per_row, kind, drill, uuid_pkg))


def generate_silkscreen_female(
    category: str,
    kind: str,
    variant: str,
    pin_count: int,
    rows: int,
) -> Polygon:
    uuid_polygon = uuid(category, kind, variant, 'polygon-contour')

    x = 1.27 * rows + line_width / 2
    top_offset = spacing / 2 + line_width / 2

    y_max, y_min = get_rectangle_bounds(pin_count, rows, spacing, top_offset, False)

    return Polygon(
        uuid=uuid_polygon,
        layer=Layer('top_legend'),
        width=Width(line_width),
        fill=Fill(False),
        grab_area=GrabArea(True),
        vertices=[
            Vertex(Position(-x, y_max), Angle(0)),
            Vertex(Position(x, y_max), Angle(0)),
            Vertex(Position(x, y_min), Angle(0)),
            Vertex(Position(-x, y_min), Angle(0)),
            Vertex(Position(-x, y_max), Angle(0)),
        ],
    )


def generate_silkscreen_male(
    category: str,
    kind: str,
    variant: str,
    pin_count: int,
    rows: int,
) -> Polygon:
    uuid_polygon = uuid(category, kind, variant, 'polygon-contour')

    per_row = pin_count // rows
    x_outer = 1.27 * rows + line_width / 2
    x_inner = x_outer - 0.27
    offset = line_width / 2

    polygon = Polygon(
        uuid=uuid_polygon,
        layer=Layer('top_legend'),
        width=Width(line_width),
        fill=Fill(False),
        grab_area=GrabArea(True),
    )

    # Start in top right corner, go around the pads clockwise
    # Down on the right
    for pin in range(1, per_row + 1):
        y = get_y(pin, per_row, 1, spacing, False)
        top_offset = offset if pin == 1 else 0
        bot_offset = offset if pin == per_row else 0
        polygon.add_vertex(Vertex(Position(x_outer, y + 1 + top_offset), Angle(0)))
        polygon.add_vertex(Vertex(Position(x_outer, y - 1 - bot_offset), Angle(0)))
        polygon.add_vertex(Vertex(Position(x_inner, y - 1.27 - bot_offset), Angle(0)))
    # Up on the left
    for pin in range(per_row, 0, -1):
        y = get_y(pin, per_row, 1, spacing, False)
        top_offset = offset if pin == 1 else 0
        bot_offset = offset if pin == per_row else 0
        polygon.add_vertex(Vertex(Position(-x_inner, y - 1.27 - bot_offset), Angle(0)))
        polygon.add_vertex(Vertex(Position(-x_outer, y - 1 - bot_offset), Angle(0)))
        polygon.add_vertex(Vertex(Position(-x_outer, y + 1 + top_offset), Angle(0)))
    # Back to start
    top_y = get_y(1, per_row, 1, spacing, False) + spacing / 2 + offset
    polygon.add_vertex(Vertex(Position(-x_inner, top_y), Angle(0)))
    polygon.add_vertex(Vertex(Position(x_inner, top_y), Angle(0)))
    polygon.add_vertex(Vertex(Position(x_outer, top_y - 0.27), Angle(0)))

    return polygon


def generate_3d_model_generic(
    model_type: str,  # male or female
    library: str,
    full_name: str,
    uuid_pkg: str,
    uuid_3d: str,
    rows: int,
    pin_count: int,
    drill: float,
) -> None:
    import cadquery as cq

    from cadquery_helpers import StepAssembly, StepColor

    print(f'Generating pkg 3D model "{full_name}": {uuid_3d}')

    insulator_height = 7.0  # Full height of female header
    standoff_height = 2.5  # Plastic part of male header
    lead_length_bottom = 3.0  # Towards bottom side
    lead_length_top_exposed = 5.5  # The exposed part towards the top of male header

    if model_type == 'female':
        # These are often slightly flat
        lead_dimensions = (0.4, drill - 0.2)
    else:
        dim = math.sqrt(((drill - 0.05) ** 2) / 2)
        lead_dimensions = (dim, dim)

    # Make base element a little longer, to get some overlap (to avoid rendering bugs when two
    # faces are in the same position)
    a_little = 0.001

    # Insulator
    if model_type == 'female':
        hole_offset = 1.0
        insulator = cq.Workplane('XY') \
            .box(spacing, spacing + a_little, insulator_height, centered=(True, True, False)) \
            .transformed(offset=(0, 0, hole_offset)) \
            .rect(spacing / 1.5, spacing / 1.5) \
            .offset2D(spacing / 20) \
            .cutBlind(insulator_height - hole_offset)
    else:
        insulator = cq.Workplane('XY') \
            .box(spacing, spacing + a_little, standoff_height, centered=(True, True, False))

    # Lead
    if model_type == 'female':
        total_lead_length = lead_length_bottom
    else:
        total_lead_length = lead_length_bottom + standoff_height + lead_length_top_exposed
    lead = cq.Workplane('XY') \
        .transformed(offset=(0, 0, -lead_length_bottom)) \
        .box(lead_dimensions[0], lead_dimensions[1], total_lead_length, centered=(True, True, False))

    # Combine into assembly
    assembly = StepAssembly(full_name)
    for pin in range(1, pin_count + 1):
        if rows == 1:
            x = 0.0
        elif rows == 2:
            x = spacing / 2 if (pin % rows == 0) else -spacing / 2
        else:
            raise RuntimeError(f'Invalid row count: {rows}')
        y = get_y(pin, pin_count, rows, spacing, False)
        location = cq.Location((x, y, 0))
        assembly.add_body(insulator, f'insulator-{pin}', StepColor.IC_BODY, location=location)
        assembly.add_body(lead, f'lead-{pin}', StepColor.LEAD_THT, location=location)

    # Save without fusing for massively better minification!
    out_path = path.join('out', library, 'pkg', uuid_pkg, f'{uuid_3d}.step')
    assembly.save(out_path, fused=False)


def generate_sym(
    library: str,
    author: str,
    name: str,
    name_lower: str,
    kind: str,
    cmpcat: str,
    keywords: str,
    rows: int,
    min_pads: int,
    max_pads: int,
    version: str,
    create_date: Optional[str],
) -> None:
    category = 'sym'
    assert rows in [1, 2]
    for i in range(min_pads, max_pads + 1, rows):
        per_row = i // rows
        w = width * rows  # Make double-row symbols wider!
        pin_length_inside = 0.6 if kind == KIND_SCREW_TERMINAL else 1.27
        pin_name_offset = 5.2 if kind == KIND_SCREW_TERMINAL else 5.08

        variant = '{}x{}'.format(rows, per_row)

        def _uuid(identifier: str) -> str:
            return uuid(category, kind, variant, identifier)

        uuid_sym = _uuid('sym')
        uuid_pins = [_uuid('pin-{}'.format(p)) for p in range(i)]
        uuid_polygon = _uuid('polygon-contour')
        uuid_decoration = _uuid('polygon-decoration')
        uuid_decoration_2 = _uuid('polygon-decoration-2')
        uuid_decoration_3 = _uuid('polygon-decoration-3')
        uuid_text_name = _uuid('text-name')
        uuid_text_value = _uuid('text-value')

        # General info
        symbol = Symbol(
            uuid_sym,
            Name('{} {}x{:02d}'.format(name, rows, per_row)),
            Description('A {}x{} {}.\n\n'
                        'Generated with {}'.format(rows, per_row, name_lower, generator)),
            Keywords('connector, {}x{}, {}'.format(rows, per_row, keywords)),
            Author(author),
            Version(version),
            Created(create_date or now()),
            Deprecated(False),
            GeneratedBy(''),
            [Category(cmpcat)],
        )

        for p in range(1, i + 1):
            x_sign = 1 if (p % rows == 0) else -1
            pin = SymbolPin(
                uuid_pins[p - 1],
                Name(str(p)),
                Position((w + 2.54) * x_sign, get_y(p, i, rows, spacing, True)),
                Rotation(180.0 if p % rows == 0 else 0),
                Length(2.54 + pin_length_inside),
                NamePosition(pin_name_offset, 0.0),
                NameRotation(0.0),
                NameHeight(2.5),
                NameAlign('left center'),
            )
            symbol.add_pin(pin)

        # Polygons
        y_max, y_min = get_rectangle_bounds(i, rows, spacing, spacing, True)
        polygon = Polygon(
            uuid_polygon,
            Layer('sym_outlines'),
            Width(line_width),
            Fill(False),
            GrabArea(True)
        )
        polygon.add_vertex(Vertex(Position(-w, y_max), Angle(0.0)))
        polygon.add_vertex(Vertex(Position(w, y_max), Angle(0.0)))
        polygon.add_vertex(Vertex(Position(w, y_min), Angle(0.0)))
        polygon.add_vertex(Vertex(Position(-w, y_min), Angle(0.0)))
        polygon.add_vertex(Vertex(Position(-w, y_max), Angle(0.0)))
        symbol.add_polygon(polygon)

        # Decorations
        if kind == KIND_HEADER:
            # Headers: Small rectangle
            for p in range(1, i + 1):
                x_sign = 1 if (p % rows == 0) else -1
                y = get_y(p, i, rows, spacing, True)
                dx = spacing / 8 * 1.5 * x_sign
                dy = spacing / 8 / 1.5
                x_offset = x_sign * (w - 1.27)
                polygon = Polygon(
                    uuid_decoration,
                    Layer('sym_outlines'),
                    Width(line_width),
                    Fill(True),
                    GrabArea(True)
                )
                polygon.add_vertex(Vertex(Position(x_offset - dx, y + dy), Angle(0.0)))
                polygon.add_vertex(Vertex(Position(x_offset + dx, y + dy), Angle(0.0)))
                polygon.add_vertex(Vertex(Position(x_offset + dx, y - dy), Angle(0.0)))
                polygon.add_vertex(Vertex(Position(x_offset - dx, y - dy), Angle(0.0)))
                polygon.add_vertex(Vertex(Position(x_offset - dx, y + dy), Angle(0.0)))
                symbol.add_polygon(polygon)
        elif kind == KIND_SOCKET:
            # Sockets: Small semicircle
            for p in range(1, i + 1):
                x_sign = 1 if (p % rows == 0) else -1
                y = get_y(p, i, rows, spacing, True)
                dy = spacing / 4 * 0.75
                x_offset = x_sign * (w - 1.27 - dy * 0.75)
                polygon = Polygon(
                    uuid_decoration,
                    Layer('sym_outlines'),
                    Width(line_width * 0.75),
                    Fill(False),
                    GrabArea(False)
                )
                polygon.add_vertex(Vertex(Position(x_offset, y - dy), Angle(x_sign * 135.0)))
                polygon.add_vertex(Vertex(Position(x_offset, y + dy), Angle(0.0)))
                symbol.add_polygon(polygon)
        elif kind == KIND_SCREW_TERMINAL:
            # Screw terminals: Screw circle
            for p in range(1, i + 1):
                y = get_y(p, i, rows, spacing, True)
                dy = spacing / 4 * 0.75
                diam = 1.6
                x_offset = w - (diam / 2) - pin_length_inside
                pos = Position(x_offset, y)
                symbol.add_circle(Circle(
                    uuid_decoration,
                    Layer('sym_outlines'),
                    Width(line_width * 0.75),
                    Fill(False),
                    GrabArea(False),
                    Diameter(diam),
                    pos,
                ))
                line_dx = (diam / 2) * math.cos(math.pi / 4 - math.pi / 16)
                line_dy = (diam / 2) * math.sin(math.pi / 4 - math.pi / 16)
                line1 = Polygon(
                    uuid_decoration_2,
                    Layer('sym_outlines'),
                    Width(line_width * .5),
                    Fill(False),
                    GrabArea(False),
                )
                line1.add_vertex(Vertex(Position(pos.x + line_dx, pos.y + line_dy), Angle(0.0)))
                line1.add_vertex(Vertex(Position(pos.x - line_dy, pos.y - line_dx), Angle(0.0)))
                symbol.add_polygon(line1)
                line2 = Polygon(
                    uuid_decoration_3,
                    Layer('sym_outlines'),
                    Width(line_width * .5),
                    Fill(False),
                    GrabArea(False),
                )
                line2.add_vertex(Vertex(Position(pos.x + line_dy, pos.y + line_dx), Angle(0.0)))
                line2.add_vertex(Vertex(Position(pos.x - line_dx, pos.y - line_dy), Angle(0.0)))
                symbol.add_polygon(line2)

        # Text
        y_max, y_min = get_rectangle_bounds(i, rows, spacing, spacing, True)
        text = Text(uuid_text_name, Layer('sym_names'), Value('{{NAME}}'), Align('center bottom'), Height(sym_text_height), Position(0.0, y_max), Rotation(0.0))
        symbol.add_text(text)

        text = Text(uuid_text_value, Layer('sym_values'), Value('{{VALUE}}'), Align('center top'), Height(sym_text_height), Position(0.0, y_min), Rotation(0.0))
        symbol.add_text(text)

        symbol.serialize(path.join('out', library, category))
        print('{}x{} {}: Wrote symbol {}'.format(rows, per_row, kind, uuid_sym))


def generate_cmp(
    library: str,
    author: str,
    name: str,
    name_lower: str,
    kind: str,
    cmpcat: str,
    keywords: str,
    default_value: str,
    rows: int,
    min_pads: int,
    max_pads: int,
    version: str,
    create_date: Optional[str],
) -> None:
    category = 'cmp'
    assert rows in [1, 2]
    for i in range(min_pads, max_pads + 1, rows):
        per_row = i // rows
        variant = '{}x{}'.format(rows, per_row)

        def _uuid(identifier: str) -> str:
            return uuid(category, kind, variant, identifier)

        uuid_cmp = _uuid('cmp')
        uuid_pins = [uuid('sym', kind, variant, 'pin-{}'.format(p)) for p in range(i)]
        uuid_signals = [_uuid('signal-{}'.format(p)) for p in range(i)]
        uuid_variant = _uuid('variant-default')
        uuid_gate = _uuid('gate-default')
        uuid_symbol = uuid('sym', kind, variant, 'sym')

        # General info
        component = Component(
            uuid_cmp,
            Name('{} {}x{:02d}'.format(name, rows, per_row)),
            Description('A {}x{} {}.\n\n'
                        'Generated with {}'.format(rows, per_row, name_lower, generator)),
            Keywords('connector, {}x{}, {}'.format(rows, per_row, keywords)),
            Author(author),
            Version(version),
            Created(create_date or now()),
            Deprecated(False),
            GeneratedBy(''),
            [Category(cmpcat)],
            SchematicOnly(False),
            DefaultValue(default_value),
            Prefix('J'),
        )

        for p in range(1, i + 1):
            component.add_signal(Signal(
                uuid_signals[p - 1],
                Name(str(p)),
                Role.PASSIVE,
                Required(False),
                Negated(False),
                Clock(False),
                ForcedNet(''),
            ))

        gate = Gate(
            uuid_gate,
            SymbolUUID(uuid_symbol),
            Position(0.0, 0.0),
            Rotation(0.0),
            Required(True),
            Suffix(''),
        )
        for p in range(1, i + 1):
            gate.add_pin_signal_map(PinSignalMap(
                uuid_pins[p - 1],
                SignalUUID(uuid_signals[p - 1]),
                TextDesignator.SYMBOL_PIN_NAME,
            ))

        component.add_variant(Variant(uuid_variant, Norm.EMPTY, Name('default'), Description(''), gate))

        # Message approvals
        if len(default_value) == 0:
            # Approve the "no default value set" message.
            component.add_approval("(approved empty_default_value)")

        component.serialize(path.join('out', library, category))
        print('{}x{} {}: Wrote component {}'.format(rows, per_row, kind, uuid_cmp))


def generate_dev(
    library: str,
    author: str,
    name: str,
    name_lower: str,
    kind: str,
    cmpcat: str,
    keywords: str,
    rows: int,
    min_pads: int,
    max_pads: int,
    pad_drills: Iterable[float],
    create_date: Optional[str],
) -> None:
    category = 'dev'
    assert rows in [1, 2]
    for i in range(min_pads, max_pads + 1, rows):
        per_row = i // rows
        for drill in pad_drills:
            lines = []

            variant = '{}x{}-D{:.1f}'.format(rows, per_row, drill)
            broad_variant = '{}x{}'.format(rows, per_row)

            def _uuid(identifier: str) -> str:
                return uuid(category, kind, variant, identifier)

            uuid_dev = _uuid('dev')
            uuid_cmp = uuid('cmp', kind, broad_variant, 'cmp')
            uuid_signals = [uuid('cmp', kind, broad_variant, 'signal-{}'.format(p)) for p in range(i)]
            uuid_pkg = uuid('pkg', kind, variant, 'pkg')
            uuid_pads = [uuid('pkg', kind, variant, 'pad-{}'.format(p)) for p in range(i)]

            # General info
            lines.append('(librepcb_device {}'.format(uuid_dev))
            lines.append(' (name "{} {}x{:02d} ⌀{:.1f}mm")'.format(name, rows, per_row, drill))
            lines.append(' (description "A {}x{} {} with {}mm pin spacing '
                         'and {:.1f}mm drill holes.\\n\\n'
                         'Generated with {}")'.format(rows, per_row, name_lower, spacing, drill, generator))
            lines.append(' (keywords "connector, {}x{}, d{:.1f}, {}")'.format(rows, per_row, drill, keywords))
            lines.append(' (author "{}")'.format(author))
            lines.append(' (version "0.1.1")')
            lines.append(' (created {})'.format(create_date or now()))
            lines.append(' (deprecated false)')
            lines.append(' (generated_by "")')
            lines.append(' (category {})'.format(cmpcat))
            lines.append(' (component {})'.format(uuid_cmp))
            lines.append(' (package {})'.format(uuid_pkg))
            signalmappings = []
            for p in range(1, i + 1):
                signalmappings.append(' (pad {} (signal {}))'.format(uuid_pads[p - 1], uuid_signals[p - 1]))
            lines.extend(sorted(signalmappings))
            lines.append(" (approved no_parts)")
            lines.append(')')

            dev_dir_path = path.join('out', library, category, uuid_dev)
            if not (path.exists(dev_dir_path) and path.isdir(dev_dir_path)):
                makedirs(dev_dir_path)
            with open(path.join(dev_dir_path, '.librepcb-dev'), 'w') as f:
                f.write('1\n')
            with open(path.join(dev_dir_path, 'device.lp'), 'w') as f:
                f.write('\n'.join(lines))
                f.write('\n')

            print('{}x{} {} ⌀{:.1f}mm: Wrote device {}'.format(rows, per_row, kind, drill, uuid_dev))


if __name__ == '__main__':
    if '--help' in sys.argv or '-h' in sys.argv:
        print(f'Usage: {sys.argv[0]} [--3d]')
        print()
        print('Options:')
        print('  --3d    Generate 3D models using cadquery')
        sys.exit(1)

    generate_3d_models = '--3d' in sys.argv
    if not generate_3d_models:
        warning = 'Note: Not generating 3D models unless the "--3d" argument is passed in!'
        print(f'\033[1;33m{warning}\033[0m')

    # Male pin headers
    generate_sym(
        library='LibrePCB_Connectors.lplib',
        author='Danilo B.',
        name='Pin Header',
        name_lower='male pin header',
        kind=KIND_HEADER,
        cmpcat='4a4e3c72-94fb-45f9-a6d8-122d2af16fb1',
        keywords='pin header, male header',
        rows=1,
        min_pads=1,
        max_pads=40,
        version='0.2',
        create_date='2018-10-17T19:13:41Z',
    )
    generate_sym(
        library='LibrePCB_Connectors.lplib',
        author='Danilo B.',
        name='Pin Header',
        name_lower='male pin header',
        kind=KIND_HEADER,
        cmpcat='4a4e3c72-94fb-45f9-a6d8-122d2af16fb1',
        keywords='pin header, male header',
        rows=2,
        min_pads=4,
        max_pads=80,
        version='0.2',
        create_date='2019-09-10T21:02:02Z',
    )
    generate_cmp(
        library='LibrePCB_Connectors.lplib',
        author='Danilo B.',
        name='Pin Header',
        name_lower='male pin header',
        kind=KIND_HEADER,
        cmpcat='4a4e3c72-94fb-45f9-a6d8-122d2af16fb1',
        keywords='pin header, male header',
        default_value='{{MPN}}',
        rows=1,
        min_pads=1,
        max_pads=40,
        version='0.1',
        create_date='2018-10-17T19:13:41Z',
    )
    generate_cmp(
        library='LibrePCB_Connectors.lplib',
        author='Danilo B.',
        name='Pin Header',
        name_lower='male pin header',
        kind=KIND_HEADER,
        cmpcat='4a4e3c72-94fb-45f9-a6d8-122d2af16fb1',
        keywords='pin header, male header',
        default_value='{{MPN}}',
        rows=2,
        min_pads=4,
        max_pads=80,
        version='0.1',
        create_date='2019-09-11T19:13:41Z',
    )
    generate_pkg(
        library='LibrePCB_Connectors.lplib',
        author='Danilo B.',
        name='Pin Header 2.54mm',
        name_lower='male pin header',
        kind=KIND_HEADER,
        assembly_type=AssemblyType.THT,
        pkgcat='e4d3a6bf-af32-48a2-b427-5e794bed949a',
        keywords='pin header, male header, tht',
        rows=1,
        min_pads=1,
        max_pads=40,
        pad_drills=[0.9, 1.0, 1.1],
        generate_silkscreen=generate_silkscreen_male,
        generate_3d_model=partial(generate_3d_model_generic, 'male'),
        generate_3d_models=generate_3d_models,
        version='0.3',
        create_date='2018-10-17T19:13:41Z',
    )
    generate_pkg(
        library='LibrePCB_Connectors.lplib',
        author='Danilo B.',
        name='Pin Header 2.54mm',
        name_lower='male pin header',
        kind=KIND_HEADER,
        assembly_type=AssemblyType.THT,
        pkgcat='e4d3a6bf-af32-48a2-b427-5e794bed949a',
        keywords='pin header, male header, tht',
        rows=2,
        min_pads=4,
        max_pads=80,
        pad_drills=[0.9, 1.0, 1.1],
        generate_silkscreen=generate_silkscreen_male,
        generate_3d_model=partial(generate_3d_model_generic, 'male'),
        generate_3d_models=generate_3d_models,
        version='0.3',
        create_date='2019-09-17T20:00:41Z',
    )
    generate_dev(
        library='LibrePCB_Connectors.lplib',
        author='Danilo B.',
        name='Generic Pin Header 2.54mm',
        name_lower='generic male pin header',
        kind=KIND_HEADER,
        cmpcat='4a4e3c72-94fb-45f9-a6d8-122d2af16fb1',
        keywords='pin header, male header, tht, generic',
        rows=1,
        min_pads=1,
        max_pads=40,
        pad_drills=[0.9, 1.0, 1.1],
        create_date='2018-10-17T19:13:41Z',
    )
    generate_dev(
        library='LibrePCB_Connectors.lplib',
        author='Danilo B.',
        name='Generic Pin Header 2.54mm',
        name_lower='generic male pin header',
        kind=KIND_HEADER,
        cmpcat='4a4e3c72-94fb-45f9-a6d8-122d2af16fb1',
        keywords='pin header, male header, tht, generic',
        rows=2,
        min_pads=4,
        max_pads=80,
        pad_drills=[0.9, 1.0, 1.1],
        create_date='2019-10-12T23:40:41Z',
    )

    # Female pin sockets
    generate_sym(
        library='LibrePCB_Connectors.lplib',
        author='Danilo B.',
        name='Pin Socket',
        name_lower='female pin socket',
        kind=KIND_SOCKET,
        cmpcat='ade6d8ff-3c4f-4dac-a939-cc540c87c280',
        keywords='pin socket, female header',
        rows=1,
        min_pads=1,
        max_pads=40,
        version='0.3',
        create_date='2018-10-17T19:13:41Z',
    )
    generate_sym(
        library='LibrePCB_Connectors.lplib',
        author='Danilo B.',
        name='Pin Socket',
        name_lower='female pin socket',
        kind=KIND_SOCKET,
        cmpcat='ade6d8ff-3c4f-4dac-a939-cc540c87c280',
        keywords='pin socket, female header',
        rows=2,
        min_pads=4,
        max_pads=80,
        version='0.3',
        create_date='2019-09-10T21:02:02Z',
    )
    generate_cmp(
        library='LibrePCB_Connectors.lplib',
        author='Danilo B.',
        name='Pin Socket',
        name_lower='female pin socket',
        kind=KIND_SOCKET,
        cmpcat='ade6d8ff-3c4f-4dac-a939-cc540c87c280',
        keywords='pin socket, female header',
        default_value='{{MPN}}',
        rows=1,
        min_pads=1,
        max_pads=40,
        version='0.1',
        create_date='2018-10-17T19:13:41Z',
    )
    generate_cmp(
        library='LibrePCB_Connectors.lplib',
        author='Danilo B.',
        name='Pin Socket',
        name_lower='female pin socket',
        kind=KIND_SOCKET,
        cmpcat='ade6d8ff-3c4f-4dac-a939-cc540c87c280',
        keywords='pin socket, female header',
        default_value='{{MPN}}',
        rows=2,
        min_pads=4,
        max_pads=80,
        version='0.1',
        create_date='2019-09-11T19:13:41Z',
    )
    generate_pkg(
        library='LibrePCB_Connectors.lplib',
        author='Danilo B.',
        name='Pin Socket 2.54mm',
        name_lower='female pin socket',
        kind=KIND_SOCKET,
        assembly_type=AssemblyType.THT,
        pkgcat='6183d171-e810-475a-a568-2a270aff8f5e',
        keywords='pin socket, female header, tht',
        rows=1,
        min_pads=1,
        max_pads=40,
        pad_drills=[0.9, 1.0, 1.1],
        generate_silkscreen=generate_silkscreen_female,
        generate_3d_model=partial(generate_3d_model_generic, 'female'),
        generate_3d_models=generate_3d_models,
        version='0.3',
        create_date='2018-10-17T19:13:41Z',
    )
    generate_pkg(
        library='LibrePCB_Connectors.lplib',
        author='Danilo B.',
        name='Pin Socket 2.54mm',
        name_lower='female pin socket',
        kind=KIND_SOCKET,
        assembly_type=AssemblyType.THT,
        pkgcat='6183d171-e810-475a-a568-2a270aff8f5e',
        keywords='pin socket, female header, tht',
        rows=2,
        min_pads=4,
        max_pads=80,
        pad_drills=[0.9, 1.0, 1.1],
        generate_silkscreen=generate_silkscreen_female,
        generate_3d_model=partial(generate_3d_model_generic, 'female'),
        generate_3d_models=generate_3d_models,
        version='0.3',
        create_date='2019-09-17T20:00:41Z',
    )
    generate_dev(
        library='LibrePCB_Connectors.lplib',
        author='Danilo B.',
        name='Generic Pin Socket 2.54mm',
        name_lower='generic female pin socket',
        kind=KIND_SOCKET,
        cmpcat='ade6d8ff-3c4f-4dac-a939-cc540c87c280',
        keywords='pin socket, female header, tht, generic',
        rows=1,
        min_pads=1,
        max_pads=40,
        pad_drills=[0.9, 1.0, 1.1],
        create_date='2018-10-17T19:13:41Z',
    )
    generate_dev(
        library='LibrePCB_Connectors.lplib',
        author='Danilo B.',
        name='Generic Pin Socket 2.54mm',
        name_lower='generic female pin socket',
        kind=KIND_SOCKET,
        cmpcat='ade6d8ff-3c4f-4dac-a939-cc540c87c280',
        keywords='pin socket, female header, tht, generic',
        rows=2,
        min_pads=4,
        max_pads=80,
        pad_drills=[0.9, 1.0, 1.1],
        create_date='2019-10-12T23:40:41Z',
    )

    # Screw terminal
    generate_sym(
        library='LibrePCB_Connectors.lplib',
        author='Danilo B.',
        name='Screw Terminal',
        name_lower='screw terminal',
        kind=KIND_SCREW_TERMINAL,
        cmpcat='f9db4ef5-2220-462a-adff-deac8402ecf0',  # Terminal Blocks
        keywords='screw terminal, terminal block',
        rows=1,
        min_pads=1,
        max_pads=40,
        version='0.2',
        create_date='2022-07-16T21:23:20Z',
    )
    generate_cmp(
        library='LibrePCB_Connectors.lplib',
        author='Danilo B.',
        name='Screw Terminal',
        name_lower='screw terminal',
        kind=KIND_SCREW_TERMINAL,
        cmpcat='f9db4ef5-2220-462a-adff-deac8402ecf0',  # Terminal Blocks
        keywords='screw terminal, terminal block',
        default_value='{{MPN}}',
        rows=1,
        min_pads=1,
        max_pads=40,
        version='0.2',
        create_date='2022-07-16T21:23:20Z',
    )

    # Generic connector
    generate_sym(
        library='LibrePCB_Connectors.lplib',
        author='Danilo B.',
        name='Connector',
        name_lower='connector',
        kind=KIND_WIRE_CONNECTOR,
        cmpcat='d0618c29-0436-42da-a388-fdadf7b23892',
        keywords='connector, generic',
        rows=1,
        min_pads=1,
        max_pads=40,
        version='0.2',
        create_date='2018-10-17T19:13:41Z',
    )

    # Soldered wire connector
    generate_cmp(
        library='LibrePCB_Connectors.lplib',
        author='Danilo B.',
        name='Soldered Wire Connector',
        name_lower='soldered wire connector',
        kind=KIND_WIRE_CONNECTOR,
        cmpcat='d0618c29-0436-42da-a388-fdadf7b23892',
        keywords='connector, soldering, generic',
        default_value='',
        rows=1,
        min_pads=1,
        max_pads=40,
        version='0.1.1',
        create_date='2018-10-17T19:13:41Z',
    )
    generate_pkg(
        library='LibrePCB_Connectors.lplib',
        author='Danilo B.',
        name='Soldered Wire Connector',
        name_lower='soldered wire connector',
        kind=KIND_WIRE_CONNECTOR,
        assembly_type=AssemblyType.NONE,
        pkgcat='56a5773f-eeb4-4b39-8cb9-274f3da26f4f',
        keywords='connector, soldering, generic',
        rows=1,
        min_pads=1,
        max_pads=40,
        pad_drills=[1.0],
        generate_silkscreen=generate_silkscreen_female,
        generate_3d_model=None,
        generate_3d_models=False,
        version='0.3',
        create_date='2018-10-17T19:13:41Z',
    )
    generate_dev(
        library='LibrePCB_Connectors.lplib',
        author='Danilo B.',
        name='Soldered Wire Connector 2.54mm',
        name_lower='generic soldered wire connector',
        kind=KIND_WIRE_CONNECTOR,
        cmpcat='d0618c29-0436-42da-a388-fdadf7b23892',
        keywords='connector, soldering, generic',
        rows=1,
        min_pads=1,
        max_pads=40,
        pad_drills=[1.0],
        create_date='2018-10-17T19:13:41Z',
    )

    save_cache(uuid_cache_file, uuid_cache)
