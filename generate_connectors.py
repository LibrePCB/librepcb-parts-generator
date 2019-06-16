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
from os import path, makedirs
from typing import Callable, List, Tuple, Iterable, Optional
from uuid import uuid4

from common import now, init_cache, save_cache, format_float as ff
from entities.common import Name, Position, Rotation, Length, Polygon, Layer, Width, Fill, GrabArea, Vertex, Angle, Description, Keywords, Author, Version, Created, Category, Text, Value, Align, Height, Deprecated
from entities.symbol import Pin as SymbolPin, Symbol
from entities.component import Component, SchematicOnly, DefaultValue, Prefix, Signal, Role, Required, Negated, Clock, ForcedNet, Gate, SymbolUUID, Suffix, Variant, Norm, PinSignalMap, SignalUUID, TextDesignator


generator = 'librepcb-parts-generator (generate_connectors.py)'

width = 2.54
spacing = 2.54
pad_size = (2.54, 1.27 * 1.25)
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


def get_y(pin_number: int, pin_count: int, spacing: float, grid_align: bool) -> float:
    """
    Return the y coordinate of the specified pin. Keep the pins grid aligned, if desired.

    The pin number is 1 index based. Pin 1 is at the top. The middle pin will
    be at or near 0.

    """
    if grid_align:
        mid = float((pin_count + 1) // 2)
    else:
        mid = (pin_count + 1) / 2
    y = -round(pin_number * spacing - mid * spacing, 2)
    if y == -0.0:  # Returns true for 0.0 too, but that doesn't matter
        return 0.0
    return y


def get_rectangle_bounds(
    pin_count: int,
    spacing: float,
    top_offset: float,
    grid_align: bool,
) -> Tuple[float, float]:
    """
    Return (y_max/y_min) of the rectangle around the pins.
    """
    if grid_align:
        even = pin_count % 2 == 0
        offset = spacing / 2 if even else 0.0
    else:
        offset = 0.0
    height = (pin_count - 1) / 2 * spacing + top_offset
    return (height - offset, -height - offset)


def generate_pkg(
    dirpath: str,
    author: str,
    name: str,
    name_lower: str,
    kind: str,
    pkgcat: str,
    keywords: str,
    min_pads: int,
    max_pads: int,
    top_offset: float,
    pad_drills: Iterable[float],
    generate_silkscreen: Callable[[List[str], str, str, str, int, float], None],
    create_date: Optional[str],
) -> None:
    category = 'pkg'
    for i in range(min_pads, max_pads + 1):
        for drill in pad_drills:
            lines = []

            variant = '1x{}-D{:.1f}'.format(i, drill)

            def _uuid(identifier: str) -> str:
                return uuid(category, kind, variant, identifier)

            uuid_pkg = _uuid('pkg')
            uuid_pads = [_uuid('pad-{}'.format(p)) for p in range(i)]
            uuid_footprint = _uuid('footprint-default')
            uuid_text_name = _uuid('text-name')
            uuid_text_value = _uuid('text-value')

            # General info
            lines.append('(librepcb_package {}'.format(uuid_pkg))
            lines.append(' (name "{} 1x{} ⌀{:.1f}mm")'.format(name, i, drill))
            lines.append(' (description "A 1x{} {} with {}mm pin spacing '
                         'and {:.1f}mm drill holes.\\n\\n'
                         'Generated with {}")'.format(i, name_lower, spacing, drill, generator))
            lines.append(' (keywords "connector, 1x{}, d{:.1f}, {}")'.format(i, drill, keywords))
            lines.append(' (author "{}")'.format(author))
            lines.append(' (version "0.1")')
            lines.append(' (created {})'.format(create_date or now()))
            lines.append(' (deprecated false)')
            lines.append(' (category {})'.format(pkgcat))
            for j in range(1, i + 1):
                lines.append(' (pad {} (name "{}"))'.format(uuid_pads[j - 1], j))
            lines.append(' (footprint {}'.format(uuid_footprint))
            lines.append('  (name "default")')
            lines.append('  (description "")')

            # Pads
            for j in range(1, i + 1):
                y = get_y(j, i, spacing, False)
                shape = 'rect' if j == 1 else 'round'
                lines.append('  (pad {} (side tht) (shape {})'.format(uuid_pads[j - 1], shape))
                lines.append('   (position 0.0 {}) (rotation 0.0) (size {} {}) (drill {})'.format(
                    y, pad_size[0], pad_size[1], drill,
                ))
                lines.append('  )')

            # Silkscreen
            generate_silkscreen(lines, category, kind, variant, i, top_offset)

            # Labels
            y_max, y_min = get_rectangle_bounds(i, spacing, top_offset + 1.27, False)
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

            pkg_dir_path = path.join(dirpath, uuid_pkg)
            if not (path.exists(pkg_dir_path) and path.isdir(pkg_dir_path)):
                makedirs(pkg_dir_path)
            with open(path.join(pkg_dir_path, '.librepcb-pkg'), 'w') as f:
                f.write('0.1\n')
            with open(path.join(pkg_dir_path, 'package.lp'), 'w') as f:
                f.write('\n'.join(lines))
                f.write('\n')

            print('1x{} {} ⌀{:.1f}mm: Wrote package {}'.format(i, kind, drill, uuid_pkg))


def generate_silkscreen_female(
    lines: List[str],
    category: str,
    kind: str,
    variant: str,
    pin_count: int,
    top_offset: float,
) -> None:
    uuid_polygon = uuid(category, kind, variant, 'polygon-contour')

    lines.append('  (polygon {} (layer top_placement)'.format(uuid_polygon))
    lines.append('   (width {}) (fill false) (grab_area true)'.format(line_width))
    y_max, y_min = get_rectangle_bounds(pin_count, spacing, top_offset, False)
    lines.append('   (vertex (position -1.27 {}) (angle 0.0))'.format(ff(y_max)))
    lines.append('   (vertex (position 1.27 {}) (angle 0.0))'.format(ff(y_max)))
    lines.append('   (vertex (position 1.27 {}) (angle 0.0))'.format(ff(y_min)))
    lines.append('   (vertex (position -1.27 {}) (angle 0.0))'.format(ff(y_min)))
    lines.append('   (vertex (position -1.27 {}) (angle 0.0))'.format(ff(y_max)))
    lines.append('  )')


def generate_silkscreen_male(
    lines: List[str],
    category: str,
    kind: str,
    variant: str,
    pin_count: int,
    top_offset: float,
) -> None:
    uuid_polygon = uuid(category, kind, variant, 'polygon-contour')

    # Start in top right corner, go around the pads clockwise
    lines.append('  (polygon {} (layer top_placement)'.format(uuid_polygon))
    lines.append('   (width {}) (fill false) (grab_area true)'.format(line_width))
    # Down on the right
    for pin in range(1, pin_count + 1):
        y = get_y(pin, pin_count, spacing, False)
        lines.append('   (vertex (position 1.27 {}) (angle 0.0))'.format(ff(y + 1)))
        lines.append('   (vertex (position 1.27 {}) (angle 0.0))'.format(ff(y - 1)))
        lines.append('   (vertex (position 1.0 {}) (angle 0.0))'.format(ff(y - 1.27)))
    # Up on the left
    for pin in range(pin_count, 0, -1):
        y = get_y(pin, pin_count, spacing, False)
        lines.append('   (vertex (position -1.0 {}) (angle 0.0))'.format(ff(y - 1.27)))
        lines.append('   (vertex (position -1.27 {}) (angle 0.0))'.format(ff(y - 1)))
        lines.append('   (vertex (position -1.27 {}) (angle 0.0))'.format(ff(y + 1)))
    # Back to start
    top_y = get_y(1, pin_count, spacing, False) + spacing / 2
    lines.append('   (vertex (position -1.0 {}) (angle 0.0))'.format(ff(top_y)))
    lines.append('   (vertex (position 1.0 {}) (angle 0.0))'.format(ff(top_y)))
    lines.append('   (vertex (position 1.27 {}) (angle 0.0))'.format(ff(top_y - 0.27)))
    lines.append('  )')


def generate_sym(
    dirpath: str,
    author: str,
    name: str,
    name_lower: str,
    kind: str,
    cmpcat: str,
    keywords: str,
    min_pads: int,
    max_pads: int,
    version: str,
    create_date: Optional[str],
) -> None:
    category = 'sym'
    for i in range(min_pads, max_pads + 1):
        variant = '1x{}'.format(i)

        def _uuid(identifier: str) -> str:
            return uuid(category, kind, variant, identifier)

        uuid_sym = _uuid('sym')
        uuid_pins = [_uuid('pin-{}'.format(p)) for p in range(i)]
        uuid_polygon = _uuid('polygon-contour')
        uuid_decoration = _uuid('polygon-decoration')
        uuid_text_name = _uuid('text-name')
        uuid_text_value = _uuid('text-value')

        # General info
        symbol = Symbol(uuid_sym,
                        Name('{} 1x{}'.format(name, i)),
                        Description('A 1x{} {}.\\n\\n'
                                    'Generated with {}'.format(i, name_lower, generator)),
                        Keywords('connector, 1x{}, {}'.format(i, keywords)),
                        Author(author),
                        Version(version),
                        Created(create_date or now()),
                        Category(cmpcat),
                        )
        for j in range(1, i + 1):
            pin = SymbolPin(uuid_pins[j - 1], Name(str(j)), Position(5.08, get_y(j, i, spacing, True)), Rotation(180.0), Length(3.81))
            symbol.add_pin(pin)

        # Polygons
        y_max, y_min = get_rectangle_bounds(i, spacing, spacing, True)
        polygon = Polygon(uuid_polygon, Layer('sym_outlines'), Width(line_width), Fill(False), GrabArea(True))
        polygon.add_vertex(Vertex(Position(-spacing, y_max), Angle(0.0)))
        polygon.add_vertex(Vertex(Position(spacing, y_max), Angle(0.0)))
        polygon.add_vertex(Vertex(Position(spacing, y_min), Angle(0.0)))
        polygon.add_vertex(Vertex(Position(-spacing, y_min), Angle(0.0)))
        polygon.add_vertex(Vertex(Position(-spacing, y_max), Angle(0.0)))
        symbol.add_polygon(polygon)

        # Decorations
        if kind == KIND_HEADER:
            # Headers: Small rectangle
            for j in range(1, i + 1):
                y = get_y(j, i, spacing, True)
                dx = spacing / 8 * 1.5
                dy = spacing / 8 / 1.5
                polygon = Polygon(uuid_decoration, Layer('sym_outlines'), Width(line_width), Fill(True), GrabArea(True))
                polygon.add_vertex(Vertex(Position(spacing / 2 - dx, y + dy), Angle(0.0)))
                polygon.add_vertex(Vertex(Position(spacing / 2 + dx, y + dy), Angle(0.0)))
                polygon.add_vertex(Vertex(Position(spacing / 2 + dx, y - dy), Angle(0.0)))
                polygon.add_vertex(Vertex(Position(spacing / 2 - dx, y - dy), Angle(0.0)))
                polygon.add_vertex(Vertex(Position(spacing / 2 - dx, y + dy), Angle(0.0)))
                symbol.add_polygon(polygon)
        elif kind == KIND_SOCKET:
            # Sockets: Small semicircle
            for j in range(1, i + 1):
                y = get_y(j, i, spacing, True)
                d = spacing / 4 * 0.75
                w = line_width * 0.75
                polygon = Polygon(uuid_decoration, Layer('sym_outlines'), Width(w), Fill(False), GrabArea(False))
                polygon.add_vertex(Vertex(Position(spacing / 2 + d * 0.5 - d - w, y - d), Angle(135.0)))
                polygon.add_vertex(Vertex(Position(spacing / 2 + d * 0.5 - d - w, y + d), Angle(0.0)))
                symbol.add_polygon(polygon)

        # Text
        y_max, y_min = get_rectangle_bounds(i, spacing, spacing, True)
        text = Text(uuid_text_name, Layer('sym_names'), Value('{{NAME}}'), Align('center bottom'), Height(sym_text_height), Position(0.0, y_max), Rotation(0.0))
        symbol.add_text(text)

        text = Text(uuid_text_value, Layer('sym_values'), Value('{{VALUE}}'), Align('center top'), Height(sym_text_height), Position(0.0, y_min), Rotation(0.0))
        symbol.add_text(text)

        sym_dir_path = path.join(dirpath, uuid_sym)
        if not (path.exists(sym_dir_path) and path.isdir(sym_dir_path)):
            makedirs(sym_dir_path)
        with open(path.join(sym_dir_path, '.librepcb-sym'), 'w') as f:
            f.write('0.1\n')
        with open(path.join(sym_dir_path, 'symbol.lp'), 'w') as f:
            f.write(str(symbol))
            f.write('\n')

        print('1x{} {}: Wrote symbol {}'.format(i, kind, uuid_sym))


def generate_cmp(
    dirpath: str,
    author: str,
    name: str,
    name_lower: str,
    kind: str,
    cmpcat: str,
    keywords: str,
    default_value: str,
    min_pads: int,
    max_pads: int,
    version: str,
    create_date: Optional[str],
) -> None:
    category = 'cmp'
    for i in range(min_pads, max_pads + 1):
        variant = '1x{}'.format(i)

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
            Name('{} 1x{}'.format(name, i)),
            Description('A 1x{} {}.\\n\\n'
                        'Generated with {}'.format(i, name_lower, generator)),
            Keywords('connector, 1x{}, {}'.format(i, keywords)),
            Author(author),
            Version(version),
            Created(create_date or now()),
            Deprecated(False),
            Category(cmpcat),
            SchematicOnly(False),
            DefaultValue(default_value),
            Prefix('J'),
        )

        for j in range(1, i + 1):
            component.add_signal(Signal(uuid_signals[j - 1], Name(str(j)), Role.PASSIVE, Required(False), Negated(False), Clock(False), ForcedNet('')))
        gate = Gate(uuid_gate, SymbolUUID(uuid_symbol), Position(0.0, 0.0), Rotation(0.0), Required(True), Suffix(''))
        for j in range(1, i + 1):
            gate.add_pin_signal_map(PinSignalMap(uuid_pins[j - 1], SignalUUID(uuid_signals[j - 1]), TextDesignator.SYMBOL_PIN_NAME))

        component.add_variant(Variant(uuid_variant, Norm.EMPTY, Name('default'), Description(''), gate))

        component.serialize(dirpath)

        print('1x{} {}: Wrote component {}'.format(i, kind, uuid_cmp))


def generate_dev(
    dirpath: str,
    author: str,
    name: str,
    name_lower: str,
    kind: str,
    cmpcat: str,
    keywords: str,
    min_pads: int,
    max_pads: int,
    pad_drills: Iterable[float],
    create_date: Optional[str],
) -> None:
    category = 'dev'
    for i in range(min_pads, max_pads + 1):
        for drill in pad_drills:
            lines = []

            variant = '1x{}-D{:.1f}'.format(i, drill)
            broad_variant = '1x{}'.format(i)

            def _uuid(identifier: str) -> str:
                return uuid(category, kind, variant, identifier)

            uuid_dev = _uuid('dev')
            uuid_cmp = uuid('cmp', kind, broad_variant, 'cmp')
            uuid_signals = [uuid('cmp', kind, broad_variant, 'signal-{}'.format(p)) for p in range(i)]
            uuid_pkg = uuid('pkg', kind, variant, 'pkg')
            uuid_pads = [uuid('pkg', kind, variant, 'pad-{}'.format(p)) for p in range(i)]

            # General info
            lines.append('(librepcb_device {}'.format(uuid_dev))
            lines.append(' (name "{} 1x{} ⌀{:.1f}mm")'.format(name, i, drill))
            lines.append(' (description "A 1x{} {} with {}mm pin spacing '
                         'and {:.1f}mm drill holes.\\n\\n'
                         'Generated with {}")'.format(i, name_lower, spacing, drill, generator))
            lines.append(' (keywords "connector, 1x{}, d{:.1f}, {}")'.format(i, drill, keywords))
            lines.append(' (author "{}")'.format(author))
            lines.append(' (version "0.1")')
            lines.append(' (created {})'.format(create_date or now()))
            lines.append(' (deprecated false)')
            lines.append(' (category {})'.format(cmpcat))
            lines.append(' (component {})'.format(uuid_cmp))
            lines.append(' (package {})'.format(uuid_pkg))
            for j in range(1, i + 1):
                lines.append(' (pad {} (signal {}))'.format(uuid_pads[j - 1], uuid_signals[j - 1]))
            lines.append(')')

            dev_dir_path = path.join(dirpath, uuid_dev)
            if not (path.exists(dev_dir_path) and path.isdir(dev_dir_path)):
                makedirs(dev_dir_path)
            with open(path.join(dev_dir_path, '.librepcb-dev'), 'w') as f:
                f.write('0.1\n')
            with open(path.join(dev_dir_path, 'device.lp'), 'w') as f:
                f.write('\n'.join(lines))
                f.write('\n')

            print('1x{} {} ⌀{:.1f}mm: Wrote device {}'.format(i, kind, drill, uuid_dev))


if __name__ == '__main__':
    def _make(dirpath: str) -> None:
        if not (path.exists(dirpath) and path.isdir(dirpath)):
            makedirs(dirpath)
    _make('out')
    _make('out/connectors')
    _make('out/connectors/pkg')
    _make('out/connectors/sym')
    generate_sym(
        dirpath='out/connectors/sym',
        author='Danilo B.',
        name='Pin Header',
        name_lower='male pin header',
        kind=KIND_HEADER,
        cmpcat='4a4e3c72-94fb-45f9-a6d8-122d2af16fb1',
        keywords='pin header, male header',
        min_pads=1,
        max_pads=40,
        version='0.2',
        create_date='2018-10-17T19:13:41Z',
    )
    generate_sym(
        dirpath='out/connectors/sym',
        author='Danilo B.',
        name='Pin Socket',
        name_lower='female pin socket',
        kind=KIND_SOCKET,
        cmpcat='ade6d8ff-3c4f-4dac-a939-cc540c87c280',
        keywords='pin socket, female header',
        min_pads=1,
        max_pads=40,
        version='0.3',
        create_date='2018-10-17T19:13:41Z',
    )
    generate_sym(
        dirpath='out/connectors/sym',
        author='Danilo B.',
        name='Connector',
        name_lower='connector',
        kind=KIND_WIRE_CONNECTOR,
        cmpcat='d0618c29-0436-42da-a388-fdadf7b23892',
        keywords='connector, generic',
        min_pads=1,
        max_pads=40,
        version='0.2',
        create_date='2018-10-17T19:13:41Z',
    )
    generate_cmp(
        dirpath='out/connectors/cmp',
        author='Danilo B.',
        name='Pin Header',
        name_lower='male pin header',
        kind=KIND_HEADER,
        cmpcat='4a4e3c72-94fb-45f9-a6d8-122d2af16fb1',
        keywords='pin header, male header',
        default_value='{{PARTNUMBER}}',
        min_pads=1,
        max_pads=40,
        version='0.1',
        create_date='2018-10-17T19:13:41Z',
    )
    generate_cmp(
        dirpath='out/connectors/cmp',
        author='Danilo B.',
        name='Pin Socket',
        name_lower='female pin socket',
        kind=KIND_SOCKET,
        cmpcat='ade6d8ff-3c4f-4dac-a939-cc540c87c280',
        keywords='pin socket, female header',
        default_value='{{PARTNUMBER}}',
        min_pads=1,
        max_pads=40,
        version='0.1',
        create_date='2018-10-17T19:13:41Z',
    )
    generate_cmp(
        dirpath='out/connectors/cmp',
        author='Danilo B.',
        name='Generic Connector',
        name_lower='soldered wire connector',
        kind=KIND_WIRE_CONNECTOR,
        cmpcat='d0618c29-0436-42da-a388-fdadf7b23892',
        keywords='connector, soldering, generic',
        default_value='',
        min_pads=1,
        max_pads=40,
        version='0.2',
        create_date='2018-10-17T19:13:41Z',
    )
    generate_pkg(
        dirpath='out/connectors/pkg',
        author='Danilo B.',
        name='Pin Socket 2.54mm',
        name_lower='female pin socket',
        kind=KIND_SOCKET,
        pkgcat='6183d171-e810-475a-a568-2a270aff8f5e',
        keywords='pin socket, female header, tht',
        min_pads=1,
        max_pads=40,
        top_offset=1.5,
        pad_drills=[0.9, 1.0, 1.1],
        generate_silkscreen=generate_silkscreen_female,
        create_date='2018-10-17T19:13:41Z',
    )
    generate_pkg(
        dirpath='out/connectors/pkg',
        author='Danilo B.',
        name='Pin Header 2.54mm',
        name_lower='male pin header',
        kind=KIND_HEADER,
        pkgcat='e4d3a6bf-af32-48a2-b427-5e794bed949a',
        keywords='pin header, male header, tht',
        min_pads=1,
        max_pads=40,
        top_offset=1.27,
        pad_drills=[0.9, 1.0, 1.1],
        generate_silkscreen=generate_silkscreen_male,
        create_date='2018-10-17T19:13:41Z',
    )
    generate_pkg(
        dirpath='out/connectors/pkg',
        author='Danilo B.',
        name='Soldered Wire Connector',
        name_lower='soldered wire connector',
        kind=KIND_WIRE_CONNECTOR,
        pkgcat='56a5773f-eeb4-4b39-8cb9-274f3da26f4f',
        keywords='connector, soldering, generic',
        min_pads=1,
        max_pads=40,
        top_offset=1.5,
        pad_drills=[1.0],
        generate_silkscreen=generate_silkscreen_female,
        create_date='2018-10-17T19:13:41Z',
    )
    generate_dev(
        dirpath='out/connectors/dev',
        author='Danilo B.',
        name='Generic Pin Socket 2.54mm',
        name_lower='generic female pin socket',
        kind=KIND_SOCKET,
        cmpcat='ade6d8ff-3c4f-4dac-a939-cc540c87c280',
        keywords='pin socket, female header, tht, generic',
        min_pads=1,
        max_pads=40,
        pad_drills=[0.9, 1.0, 1.1],
        create_date='2018-10-17T19:13:41Z',
    )
    generate_dev(
        dirpath='out/connectors/dev',
        author='Danilo B.',
        name='Generic Pin Header 2.54mm',
        name_lower='generic male pin header',
        kind=KIND_HEADER,
        cmpcat='4a4e3c72-94fb-45f9-a6d8-122d2af16fb1',
        keywords='pin header, male header, tht, generic',
        min_pads=1,
        max_pads=40,
        pad_drills=[0.9, 1.0, 1.1],
        create_date='2018-10-17T19:13:41Z',
    )
    generate_dev(
        dirpath='out/connectors/dev',
        author='Danilo B.',
        name='Soldered Wire Connector 2.54mm',
        name_lower='generic soldered wire connector',
        kind=KIND_WIRE_CONNECTOR,
        cmpcat='d0618c29-0436-42da-a388-fdadf7b23892',
        keywords='connector, soldering, generic',
        min_pads=1,
        max_pads=40,
        pad_drills=[1.0],
        create_date='2018-10-17T19:13:41Z',
    )
    # TODO: Generate sym, cmp and dev for soldered wire connector
    save_cache(uuid_cache_file, uuid_cache)
