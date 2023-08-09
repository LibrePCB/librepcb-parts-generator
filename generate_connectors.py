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
from os import makedirs, path
from uuid import uuid4

from typing import Callable, Iterable, List, Optional, Tuple

from common import format_float as ff
from common import init_cache, now, save_cache
from entities.common import (
    Align, Angle, Author, Category, Created, Deprecated, Description, Fill, GrabArea, Height, Keywords, Layer, Length,
    Name, Polygon, Position, Rotation, Text, Value, Version, Vertex, Width
)
from entities.component import (
    Clock, Component, DefaultValue, ForcedNet, Gate, Negated, Norm, PinSignalMap, Prefix, Required, Role, SchematicOnly,
    Signal, SignalUUID, Suffix, SymbolUUID, TextDesignator, Variant
)
from entities.symbol import Pin as SymbolPin
from entities.symbol import Symbol

generator = 'librepcb-parts-generator (generate_connectors.py)'

width = 2.54
spacing = 2.54
pad_size = (2.54 - 0.35, 1.27 * 1.25)
line_width = 0.25
pkg_text_height = 1.0
sym_text_height = 2.54


KIND_HEADER = 'pinheader'
KIND_SOCKET = 'pinsocket'
KIND_WIRE_CONNECTOR = 'wireconnector'


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
    be at or near 0.

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
    pkgcat: str,
    keywords: str,
    rows: int,
    min_pads: int,
    max_pads: int,
    pad_drills: Iterable[float],
    generate_silkscreen: Callable[[List[str], str, str, str, int, int], None],
    version: str,
    create_date: Optional[str],
) -> None:
    category = 'pkg'
    assert rows in [1, 2]
    for i in range(min_pads, max_pads + 1, rows):
        for drill in pad_drills:
            per_row = i // rows
            top_offset = spacing / 2

            variant = '{}x{}-D{:.1f}'.format(rows, per_row, drill)

            lines = []

            def _uuid(identifier: str) -> str:
                return uuid(category, kind, variant, identifier)

            uuid_pkg = _uuid('pkg')
            uuid_pads = [_uuid('pad-{}'.format(p)) for p in range(i)]
            uuid_footprint = _uuid('footprint-default')
            uuid_text_name = _uuid('text-name')
            uuid_text_value = _uuid('text-value')

            # General info
            lines.append('(librepcb_package {}'.format(uuid_pkg))
            lines.append(' (name "{} {}x{:02d} ⌀{:.1f}mm")'.format(name, rows, per_row, drill))
            lines.append(' (description "A {}x{} {} with {}mm pin spacing '
                         'and {:.1f}mm drill holes.\\n\\n'
                         'Generated with {}")'.format(rows, per_row, name_lower, spacing, drill, generator))
            lines.append(' (keywords "connector, {}x{}, d{:.1f}, {}")'.format(rows, per_row, drill, keywords))
            lines.append(' (author "{}")'.format(author))
            lines.append(' (version "{}")'.format(version))
            lines.append(' (created {})'.format(create_date or now()))
            lines.append(' (deprecated false)')
            lines.append(' (category {})'.format(pkgcat))
            for j in range(1, i + 1):
                lines.append(' (pad {} (name "{}"))'.format(uuid_pads[j - 1], j))
            lines.append(' (footprint {}'.format(uuid_footprint))
            lines.append('  (name "default")')
            lines.append('  (description "")')

            # Pads
            for p in range(1, i + 1):
                if rows == 1:
                    x = 0.0
                elif rows == 2:
                    x = spacing / 2 if (p % rows == 0) else -spacing / 2
                y = get_y(p, i, rows, spacing, False)
                shape = 'rect' if p == 1 else 'round'
                lines.append('  (pad {} (side tht) (shape {})'.format(uuid_pads[p - 1], shape))
                lines.append('   (position {} {}) (rotation 0.0) (size {} {}) (drill {})'.format(
                    ff(x), ff(y), ff(pad_size[0]), ff(pad_size[1]), drill,
                ))
                lines.append('  )')

            # Silkscreen
            generate_silkscreen(lines, category, kind, variant, i, rows)

            # Labels
            y_max, y_min = get_rectangle_bounds(i, rows, spacing, top_offset + 1.27, False)
            text_attrs = '(height {}) (stroke_width 0.2) ' \
                         '(letter_spacing auto) (line_spacing auto)'.format(pkg_text_height)
            lines.append('  (stroke_text {} (layer top_names)'.format(uuid_text_name))
            lines.append('   {}'.format(text_attrs))
            lines.append('   (align center bottom) (position 0.0 {}) (rotation 0.0)'.format(
                ff(y_max),
            ))
            lines.append('   (auto_rotate true) (mirror false) (value "{{NAME}}")')
            lines.append('  )')
            lines.append('  (stroke_text {} (layer top_values)'.format(uuid_text_value))
            lines.append('   {}'.format(text_attrs))
            lines.append('   (align center top) (position 0.0 {}) (rotation 0.0)'.format(
                ff(y_min),
            ))
            lines.append('   (auto_rotate true) (mirror false) (value "{{VALUE}}")')
            lines.append('  )')

            lines.append(' )')
            lines.append(')')

            pkg_dir_path = path.join('out', library, category, uuid_pkg)
            if not (path.exists(pkg_dir_path) and path.isdir(pkg_dir_path)):
                makedirs(pkg_dir_path)
            with open(path.join(pkg_dir_path, '.librepcb-pkg'), 'w') as f:
                f.write('0.1\n')
            with open(path.join(pkg_dir_path, 'package.lp'), 'w') as f:
                f.write('\n'.join(lines))
                f.write('\n')

            print('{}x{:02d} {} ⌀{:.1f}mm: Wrote package {}'.format(rows, per_row, kind, drill, uuid_pkg))


def generate_silkscreen_female(
    lines: List[str],
    category: str,
    kind: str,
    variant: str,
    pin_count: int,
    rows: int,
) -> None:
    uuid_polygon = uuid(category, kind, variant, 'polygon-contour')

    x = 1.27 * rows + line_width / 2
    top_offset = spacing / 2 + line_width / 2

    lines.append('  (polygon {} (layer top_placement)'.format(uuid_polygon))
    lines.append('   (width {}) (fill false) (grab_area true)'.format(line_width))
    y_max, y_min = get_rectangle_bounds(pin_count, rows, spacing, top_offset, False)
    lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(ff(x), ff(y_max)))
    lines.append('   (vertex (position {} {}) (angle 0.0))'.format(ff(x), ff(y_max)))
    lines.append('   (vertex (position {} {}) (angle 0.0))'.format(ff(x), ff(y_min)))
    lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(ff(x), ff(y_min)))
    lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(ff(x), ff(y_max)))
    lines.append('  )')


def generate_silkscreen_male(
    lines: List[str],
    category: str,
    kind: str,
    variant: str,
    pin_count: int,
    rows: int,
) -> None:
    uuid_polygon = uuid(category, kind, variant, 'polygon-contour')

    per_row = pin_count // rows
    x_outer = 1.27 * rows + line_width / 2
    x_inner = x_outer - 0.27
    offset = line_width / 2

    # Start in top right corner, go around the pads clockwise
    lines.append('  (polygon {} (layer top_placement)'.format(uuid_polygon))
    lines.append('   (width {}) (fill false) (grab_area true)'.format(line_width))
    # Down on the right
    for pin in range(1, per_row + 1):
        y = get_y(pin, per_row, 1, spacing, False)
        top_offset = offset if pin == 1 else 0
        bot_offset = offset if pin == per_row else 0
        lines.append('   (vertex (position {} {}) (angle 0.0))'.format(ff(x_outer), ff(y + 1 + top_offset)))
        lines.append('   (vertex (position {} {}) (angle 0.0))'.format(ff(x_outer), ff(y - 1 - bot_offset)))
        lines.append('   (vertex (position {} {}) (angle 0.0))'.format(ff(x_inner), ff(y - 1.27 - bot_offset)))
    # Up on the left
    for pin in range(per_row, 0, -1):
        y = get_y(pin, per_row, 1, spacing, False)
        top_offset = offset if pin == 1 else 0
        bot_offset = offset if pin == per_row else 0
        lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(ff(x_inner), ff(y - 1.27 - bot_offset)))
        lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(ff(x_outer), ff(y - 1 - bot_offset)))
        lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(ff(x_outer), ff(y + 1 + top_offset)))
    # Back to start
    top_y = get_y(1, per_row, 1, spacing, False) + spacing / 2 + offset
    lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(ff(x_inner), ff(top_y)))
    lines.append('   (vertex (position {} {}) (angle 0.0))'.format(ff(x_inner), ff(top_y)))
    lines.append('   (vertex (position {} {}) (angle 0.0))'.format(ff(x_outer), ff(top_y - 0.27)))
    lines.append('  )')


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

        variant = '{}x{}'.format(rows, per_row)

        def _uuid(identifier: str) -> str:
            return uuid(category, kind, variant, identifier)

        uuid_sym = _uuid('sym')
        uuid_pins = [_uuid('pin-{}'.format(p)) for p in range(i)]
        uuid_polygon = _uuid('polygon-contour')
        uuid_decoration = _uuid('polygon-decoration')
        uuid_text_name = _uuid('text-name')
        uuid_text_value = _uuid('text-value')

        # General info
        symbol = Symbol(
            uuid_sym,
            Name('{} {}x{:02d}'.format(name, rows, per_row)),
            Description('A {}x{} {}.\\n\\n'
                        'Generated with {}'.format(rows, per_row, name_lower, generator)),
            Keywords('connector, {}x{}, {}'.format(rows, per_row, keywords)),
            Author(author),
            Version(version),
            Created(create_date or now()),
            Category(cmpcat),
        )

        for p in range(1, i + 1):
            x_sign = 1 if (p % rows == 0) else -1
            pin = SymbolPin(
                uuid_pins[p - 1],
                Name(str(p)),
                Position((w + 2.54) * x_sign, get_y(p, i, rows, spacing, True)),
                Rotation(180.0 if p % rows == 0 else 0),
                Length(3.81)
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

        # Text
        y_max, y_min = get_rectangle_bounds(i, rows, spacing, spacing, True)
        text = Text(uuid_text_name, Layer('sym_names'), Value('{{NAME}}'), Align('center bottom'), Height(sym_text_height), Position(0.0, y_max), Rotation(0.0))
        symbol.add_text(text)

        text = Text(uuid_text_value, Layer('sym_values'), Value('{{VALUE}}'), Align('center top'), Height(sym_text_height), Position(0.0, y_min), Rotation(0.0))
        symbol.add_text(text)

        sym_dir_path = path.join('out', library, category, uuid_sym)
        if not (path.exists(sym_dir_path) and path.isdir(sym_dir_path)):
            makedirs(sym_dir_path)
        with open(path.join(sym_dir_path, '.librepcb-sym'), 'w') as f:
            f.write('0.1\n')
        with open(path.join(sym_dir_path, 'symbol.lp'), 'w') as f:
            f.write(str(symbol))
            f.write('\n')

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
            Description('A {}x{} {}.\\n\\n'
                        'Generated with {}'.format(rows, per_row, name_lower, generator)),
            Keywords('connector, {}x{}, {}'.format(rows, per_row, keywords)),
            Author(author),
            Version(version),
            Created(create_date or now()),
            Deprecated(False),
            Category(cmpcat),
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
            lines.append(' (version "0.1")')
            lines.append(' (created {})'.format(create_date or now()))
            lines.append(' (deprecated false)')
            lines.append(' (category {})'.format(cmpcat))
            lines.append(' (component {})'.format(uuid_cmp))
            lines.append(' (package {})'.format(uuid_pkg))
            signalmappings = []
            for p in range(1, i + 1):
                signalmappings.append(' (pad {} (signal {}))'.format(uuid_pads[p - 1], uuid_signals[p - 1]))
            lines.extend(sorted(signalmappings))
            lines.append(')')

            dev_dir_path = path.join('out', library, category, uuid_dev)
            if not (path.exists(dev_dir_path) and path.isdir(dev_dir_path)):
                makedirs(dev_dir_path)
            with open(path.join(dev_dir_path, '.librepcb-dev'), 'w') as f:
                f.write('0.1\n')
            with open(path.join(dev_dir_path, 'device.lp'), 'w') as f:
                f.write('\n'.join(lines))
                f.write('\n')

            print('{}x{} {} ⌀{:.1f}mm: Wrote device {}'.format(rows, per_row, kind, drill, uuid_dev))


if __name__ == '__main__':
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
        default_value='{{PARTNUMBER}}',
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
        default_value='{{PARTNUMBER}}',
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
        pkgcat='e4d3a6bf-af32-48a2-b427-5e794bed949a',
        keywords='pin header, male header, tht',
        rows=1,
        min_pads=1,
        max_pads=40,
        pad_drills=[0.9, 1.0, 1.1],
        generate_silkscreen=generate_silkscreen_male,
        version='0.2',
        create_date='2018-10-17T19:13:41Z',
    )
    generate_pkg(
        library='LibrePCB_Connectors.lplib',
        author='Danilo B.',
        name='Pin Header 2.54mm',
        name_lower='male pin header',
        kind=KIND_HEADER,
        pkgcat='e4d3a6bf-af32-48a2-b427-5e794bed949a',
        keywords='pin header, male header, tht',
        rows=2,
        min_pads=4,
        max_pads=80,
        pad_drills=[0.9, 1.0, 1.1],
        generate_silkscreen=generate_silkscreen_male,
        version='0.2',
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
        default_value='{{PARTNUMBER}}',
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
        default_value='{{PARTNUMBER}}',
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
        pkgcat='6183d171-e810-475a-a568-2a270aff8f5e',
        keywords='pin socket, female header, tht',
        rows=1,
        min_pads=1,
        max_pads=40,
        pad_drills=[0.9, 1.0, 1.1],
        generate_silkscreen=generate_silkscreen_female,
        version='0.2',
        create_date='2018-10-17T19:13:41Z',
    )
    generate_pkg(
        library='LibrePCB_Connectors.lplib',
        author='Danilo B.',
        name='Pin Socket 2.54mm',
        name_lower='female pin socket',
        kind=KIND_SOCKET,
        pkgcat='6183d171-e810-475a-a568-2a270aff8f5e',
        keywords='pin socket, female header, tht',
        rows=2,
        min_pads=4,
        max_pads=80,
        pad_drills=[0.9, 1.0, 1.1],
        generate_silkscreen=generate_silkscreen_female,
        version='0.2',
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
        version='0.1',
        create_date='2018-10-17T19:13:41Z',
    )
    generate_pkg(
        library='LibrePCB_Connectors.lplib',
        author='Danilo B.',
        name='Soldered Wire Connector',
        name_lower='soldered wire connector',
        kind=KIND_WIRE_CONNECTOR,
        pkgcat='56a5773f-eeb4-4b39-8cb9-274f3da26f4f',
        keywords='connector, soldering, generic',
        rows=1,
        min_pads=1,
        max_pads=40,
        pad_drills=[1.0],
        generate_silkscreen=generate_silkscreen_female,
        version='0.2',
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
