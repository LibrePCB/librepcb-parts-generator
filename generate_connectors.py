"""
Generate pin header and socket packages.

             +---+- width
             v   v
             +---+ <-+
             |   |   | top
          +->| O | <-+
  spacing |  |(…)|
          +->| O |
             |   |
             +---+

"""
from datetime import datetime
from os import path, makedirs
from typing import Callable, List, Tuple
from uuid import uuid4

import common

generator = 'librepcb-parts-generator (generate_connectors.py)'
author = 'librepcb-parts-generator'

width = 2.54
spacing = 2.54
pad_drill = 1.0
pad_size = (2.54, 1.27 * 1.25)
line_width = 0.25
footprint_text_height = 1.0
symbol_text_height = 2.54
decoration_size = 2.54 / 4


# Initialize UUID cache
uuid_cache_file = 'uuid_cache_connectors.csv'
uuid_cache = common.init_cache(uuid_cache_file)


def now() -> str:
    """
    Return current timestamp as string.
    """
    return datetime.utcnow().isoformat() + 'Z'


def uuid(kind: str, typ: str, pin_number: int, identifier: str = None) -> str:
    """
    Return a uuid for the specified pin.
    """
    if identifier:
        key = '{}-{}-1x{}-{}'.format(kind, typ, pin_number, identifier).lower().replace(' ', '~')
    else:
        key = '{}-{}-1x{}'.format(kind, typ, pin_number).lower().replace(' ', '~')
    if key not in uuid_cache:
        uuid_cache[key] = str(uuid4())
    return uuid_cache[key]


def get_y(pin_number: int, pin_count: int, spacing: float):
    """
    Return the y coordinate of the specified pin. Keep the pins grid aligned.

    The pin number is 1 index based. Pin 1 is at the top. The middle pin will
    be at or near 0.

    """
    mid = (pin_count + 1) // 2
    return -round(pin_number * spacing - mid * spacing, 2)


def get_rectangle_bounds(pin_count: int, spacing: float, top_offset: float) -> Tuple[float, float]:
    """
    Return (y_max/y_min) of the rectangle around the pins.
    """
    even = pin_count % 2 == 0
    offset = spacing / 2 if even else 0
    height = (pin_count - 1) / 2 * spacing + top_offset
    return (height - offset, -height - offset)


def generate_pkg(
    dirpath: str,
    name: str,
    name_lower: str,
    kind: str,
    pkgcat: str,
    keywords: str,
    min_pads: int,
    max_pads: int,
    top_offset: float,
    generate_silkscreen: Callable[[List[str], str, int, float], None]
):
    for i in range(min_pads, max_pads + 1):
        lines = []

        pkg_uuid = uuid(kind, 'pkg', i)

        # General info
        lines.append('(librepcb_package {}'.format(pkg_uuid))
        lines.append(' (name "{} 1x{}")'.format(name, i))
        lines.append(' (description "A 1x{} {} with {}mm pin spacing.\\n\\n'
                     'Generated with {}")'.format(i, name_lower, spacing, generator))
        lines.append(' (keywords "connector, 1x{}, {}")'.format(i, keywords))
        lines.append(' (author "{}")'.format(author))
        lines.append(' (version "0.1")')
        lines.append(' (created {})'.format(now()))
        lines.append(' (deprecated false)')
        lines.append(' (category {})'.format(pkgcat))
        pad_uuids = [uuid(kind, 'pad', i, str(p)) for p in range(i)]
        for j in range(1, i + 1):
            lines.append(' (pad {} (name "{}"))'.format(pad_uuids[j - 1], j))
        lines.append(' (footprint {}'.format(uuid(kind, 'footprint', i, 'default')))
        lines.append('  (name "default")')
        lines.append('  (description "")')

        # Pads
        for j in range(1, i + 1):
            y = get_y(j, i, spacing)
            shape = 'rect' if j == 1 else 'round'
            lines.append('  (pad {} (side tht) (shape {})'.format(pad_uuids[j - 1], shape))
            lines.append('   (pos 0.0 {}) (rot 0.0) (size {} {}) (drill {})'.format(
                y, pad_size[0], pad_size[1], pad_drill,
            ))
            lines.append('  )')

        # Silkscreen
        generate_silkscreen(lines, kind, i, top_offset)

        # Labels
        y_max, y_min = get_rectangle_bounds(i, spacing, top_offset + 1.27)
        text_attrs = '(height {}) (stroke_width 0.2) ' \
                     '(letter_spacing auto) (line_spacing auto)'.format(footprint_text_height)
        lines.append('  (stroke_text {} (layer top_names)'.format(uuid(kind, 'label-name', i)))
        lines.append('   {}'.format(text_attrs))
        lines.append('   (align center bottom) (pos 0.0 {}) (rot 0.0) (auto_rotate true)'.format(
            y_max,
        ))
        lines.append('   (mirror false) (value "{{NAME}}")')
        lines.append('  )')
        lines.append('  (stroke_text {} (layer top_values)'.format(uuid(kind, 'label-value', i)))
        lines.append('   {}'.format(text_attrs))
        lines.append('   (align center top) (pos 0.0 {}) (rot 0.0) (auto_rotate true)'.format(
            y_min,
        ))
        lines.append('   (mirror false) (value "{{VALUE}}")')
        lines.append('  )')

        lines.append(' )')
        lines.append(')')

        pkg_dir_path = path.join(dirpath, pkg_uuid)
        if not (path.exists(pkg_dir_path) and path.isdir(pkg_dir_path)):
            makedirs(pkg_dir_path)
        with open(path.join(pkg_dir_path, '.librepcb-pkg'), 'w') as f:
            f.write('0.1\n')
        with open(path.join(pkg_dir_path, 'package.lp'), 'w') as f:
            f.write('\n'.join(lines))
            f.write('\n')

        print('1x{}: Wrote package {}'.format(i, pkg_uuid))


def generate_silkscreen_female(
    lines: List[str],
    kind: str,
    pin_count: int,
    top_offset: float,
) -> None:
    lines.append('  (polygon {} (layer top_placement)'.format(
        uuid(kind, 'polygon', pin_count, 'contour')
    ))
    lines.append('   (width {}) (fill false) (grab true)'.format(line_width))
    y_max, y_min = get_rectangle_bounds(pin_count, spacing, top_offset)
    lines.append('   (vertex (pos -1.27 {}) (angle 0.0))'.format(y_max))
    lines.append('   (vertex (pos 1.27 {}) (angle 0.0))'.format(y_max))
    lines.append('   (vertex (pos 1.27 {}) (angle 0.0))'.format(y_min))
    lines.append('   (vertex (pos -1.27 {}) (angle 0.0))'.format(y_min))
    lines.append('   (vertex (pos -1.27 {}) (angle 0.0))'.format(y_max))
    lines.append('  )')


def generate_silkscreen_male(
    lines: List[str],
    kind: str,
    pin_count: int,
    top_offset: float,
) -> None:
    # Start in top right corner, go around the pads clockwise
    lines.append('  (polygon {} (layer top_placement)'.format(
        uuid(kind, 'polygon', pin_count, 'contour')
    ))
    lines.append('   (width {}) (fill false) (grab true)'.format(line_width))
    # Down on the right
    for pin in range(1, pin_count + 1):
        y = get_y(pin, pin_count, spacing)
        lines.append('   (vertex (pos 1.27 {}) (angle 0.0))'.format(y + 1))
        lines.append('   (vertex (pos 1.27 {}) (angle 0.0))'.format(y - 1))
        lines.append('   (vertex (pos 1.0 {}) (angle 0.0))'.format(y - 1.27))
    # Up on the left
    for pin in range(pin_count, 0, -1):
        y = get_y(pin, pin_count, spacing)
        lines.append('   (vertex (pos -1.0 {}) (angle 0.0))'.format(y - 1.27))
        lines.append('   (vertex (pos -1.27 {}) (angle 0.0))'.format(y - 1))
        lines.append('   (vertex (pos -1.27 {}) (angle 0.0))'.format(y + 1))
    # Back to start
    top_y = get_y(1, pin_count, spacing) + spacing / 2
    lines.append('   (vertex (pos -1.0 {}) (angle 0.0))'.format(top_y))
    lines.append('   (vertex (pos 1.0 {}) (angle 0.0))'.format(top_y))
    lines.append('   (vertex (pos 1.27 {}) (angle 0.0))'.format(top_y - 0.27))
    lines.append('  )')


def generate_sym(
    dirpath: str,
    name: str,
    name_lower: str,
    kind: str,
    cmpcat: str,
    keywords: str,
    min_pads: int,
    max_pads: int,
):
    for i in range(min_pads, max_pads + 1):
        lines = []

        sym_uuid = uuid(kind, 'sym', i)

        # General info
        lines.append('(librepcb_symbol {}'.format(sym_uuid))
        lines.append(' (name "{} 1x{}")'.format(name, i))
        lines.append(' (description "A 1x{} {}.\\n\\n'
                     'Generated with {}")'.format(i, name_lower, generator))
        lines.append(' (keywords "connector, 1x{}, {}")'.format(i, keywords))
        lines.append(' (author "{}")'.format(author))
        lines.append(' (version "0.1")')
        lines.append(' (created {})'.format(now()))
        lines.append(' (deprecated false)')
        lines.append(' (category {})'.format(cmpcat))
        pin_uuids = [uuid(kind, 'pin', i, str(p)) for p in range(i)]
        for j in range(1, i + 1):
            lines.append(' (pin {} (name "{}")'.format(pin_uuids[j - 1], j))
            lines.append('  (position 5.08 {}) (rotation 180.0) (length 3.81)'.format(
                get_y(j, i, spacing)
            ))
            lines.append(' )')

        # Polygons
        y_max, y_min = get_rectangle_bounds(i, spacing, spacing)
        lines.append(' (polygon {} (layer sym_outlines)'.format(
            uuid(kind, 'polygon', i, 'sym-outline')
        ))
        lines.append('  (width {}) (fill false) (grab true)'.format(line_width))
        lines.append('  (vertex (pos -{} {}) (angle 0.0))'.format(spacing, y_max))
        lines.append('  (vertex (pos {} {}) (angle 0.0))'.format(spacing, y_max))
        lines.append('  (vertex (pos {} {}) (angle 0.0))'.format(spacing, y_min))
        lines.append('  (vertex (pos -{} {}) (angle 0.0))'.format(spacing, y_min))
        lines.append('  (vertex (pos -{} {}) (angle 0.0))'.format(spacing, y_max))
        lines.append(' )')

        # Decorations
        if kind == 'pinheader':
            # Headers: Small rectangle
            for j in range(1, i + 1):
                y = get_y(j, i, spacing)
                dx = spacing / 8 * 1.5
                dy = spacing / 8 / 1.5
                lines.append(' (polygon {} (layer sym_outlines)'.format(
                    uuid(kind, 'polygon', i, 'sym_decoration')
                ))
                lines.append('  (width {}) (fill true) (grab true)'.format(line_width))
                vertex = '  (vertex (pos {} {}) (angle 0.0))'
                lines.append(vertex.format(spacing / 2 - dx, y + dy))
                lines.append(vertex.format(spacing / 2 + dx, y + dy))
                lines.append(vertex.format(spacing / 2 + dx, y - dy))
                lines.append(vertex.format(spacing / 2 - dx, y - dy))
                lines.append(vertex.format(spacing / 2 - dx, y + dy))
                lines.append(' )')
        elif kind == 'pinsocket':
            # Sockets: Small semicircle
            for j in range(1, i + 1):
                y = get_y(j, i, spacing)
                d = spacing / 4 * 0.75
                w = line_width * 0.75
                lines.append(' (polygon {} (layer sym_outlines)'.format(
                    uuid(kind, 'polygon', i, 'sym_decoration')
                ))
                lines.append('  (width {}) (fill false) (grab false) '.format(w))
                lines.append('  (vertex (pos {} {}) (angle 135.0))'.format(
                    spacing / 2 + d * 0.5 - d - w, y - d),
                )
                lines.append('  (vertex (pos {} {}) (angle 0.0))'.format(
                    spacing / 2 + d * 0.5 - d - w, y + d)
                )
                lines.append(' )')

        # Text
        y_max, y_min = get_rectangle_bounds(i, spacing, spacing)
        lines.append(' (text {} (layer sym_names) (value "{{{{NAME}}}}")'.format(
            uuid(kind, 'text-name', i)),
        )
        lines.append('  (align center bottom) (height {}) (position 0.0 {}) (rotation 0.0)'.format(
            symbol_text_height, y_max,
        ))
        lines.append(' )')
        lines.append(' (text {} (layer sym_names) (value "{{{{VALUE}}}}")'.format(
            uuid(kind, 'text-value', i)),
        )
        lines.append('  (align center top) (height {}) (position 0.0 {}) (rotation 0.0)'.format(
            symbol_text_height, y_min,
        ))
        lines.append(' )')

        lines.append(')')

        sym_dir_path = path.join(dirpath, sym_uuid)
        if not (path.exists(sym_dir_path) and path.isdir(sym_dir_path)):
            makedirs(sym_dir_path)
        with open(path.join(sym_dir_path, '.librepcb-sym'), 'w') as f:
            f.write('0.1\n')
        with open(path.join(sym_dir_path, 'symbol.lp'), 'w') as f:
            f.write('\n'.join(lines))
            f.write('\n')

        print('1x{}: Wrote symbol {}'.format(i, sym_uuid))


def generate_cmp(
    dirpath: str,
    name: str,
    name_lower: str,
    kind: str,
    cmpcat: str,
    keywords: str,
    min_pads: int,
    max_pads: int,
):
    for i in range(min_pads, max_pads + 1):
        lines = []

        cmp_uuid = uuid(kind, 'cmp', i)

        # General info
        lines.append('(librepcb_component {}'.format(cmp_uuid))
        lines.append(' (name "{} 1x{}")'.format(name, i))
        lines.append(' (description "A 1x{} {}.\\n\\n'
                     'Generated with {}")'.format(i, name_lower, generator))
        lines.append(' (keywords "connector, 1x{}, {}")'.format(i, keywords))
        lines.append(' (author "{}")'.format(author))
        lines.append(' (version "0.1")')
        lines.append(' (created {})'.format(now()))
        lines.append(' (deprecated false)')
        lines.append(' (category {})'.format(cmpcat))
        lines.append(' (schematic_only false)')
        lines.append(' (default_value "")')
        lines.append(' (prefix "J")')

        pin_uuids = [uuid(kind, 'pin', i, str(p)) for p in range(i)]
        signal_uuids = [uuid(kind, 'signal', i, str(p)) for p in range(i)]
        variant_uuid = uuid(kind, 'cmp-variant', i)
        gate_uuid = uuid(kind, 'cmp-gate', i)
        symbol_uuid = uuid(kind, 'sym', i)

        for j in range(1, i + 1):
            lines.append(' (signal {} (name "{}") (role passive)'.format(signal_uuids[j - 1], j))
            lines.append('  (required false) (negated false) (clock false) (forced_net "")')
            lines.append(' )')
        lines.append(' (variant {} (norm "")'.format(variant_uuid))
        lines.append('  (name "default")')
        lines.append('  (description "")')
        lines.append('  (gate {}'.format(gate_uuid))
        lines.append('   (symbol {})'.format(symbol_uuid))
        lines.append('   (position 0.0 0.0) (rotation 0.0) (required true) (suffix "")')
        for j in range(1, i + 1):
            lines.append('   (pin {} (signal {}) (text pin))'.format(
                pin_uuids[j - 1],
                signal_uuids[j - 1],
            ))
        lines.append('  )')
        lines.append(' )')
        lines.append(')')

        cmp_dir_path = path.join(dirpath, cmp_uuid)
        if not (path.exists(cmp_dir_path) and path.isdir(cmp_dir_path)):
            makedirs(cmp_dir_path)
        with open(path.join(cmp_dir_path, '.librepcb-cmp'), 'w') as f:
            f.write('0.1\n')
        with open(path.join(cmp_dir_path, 'component.lp'), 'w') as f:
            f.write('\n'.join(lines))
            f.write('\n')

        print('1x{}: Wrote component {}'.format(i, cmp_uuid))


if __name__ == '__main__':
    def _make(dirpath: str):
        if not (path.exists(dirpath) and path.isdir(dirpath)):
            makedirs(dirpath)
    _make('out')
    _make('out/connectors')
    _make('out/connectors/pkg')
    _make('out/connectors/sym')
    generate_sym(
        dirpath='out/connectors/sym',
        name='Pin Header',
        name_lower='male pin header',
        kind='pinheader',
        cmpcat='4a4e3c72-94fb-45f9-a6d8-122d2af16fb1',
        keywords='pin header, male header',
        min_pads=1,
        max_pads=40,
    )
    generate_sym(
        dirpath='out/connectors/sym',
        name='Pin Socket',
        name_lower='female pin socket',
        kind='pinsocket',
        cmpcat='ade6d8ff-3c4f-4dac-a939-cc540c87c280',
        keywords='pin socket, female header',
        min_pads=1,
        max_pads=40,
    )
    generate_cmp(
        dirpath='out/connectors/cmp',
        name='Pin Header',
        name_lower='male pin header',
        kind='pinheader',
        cmpcat='4a4e3c72-94fb-45f9-a6d8-122d2af16fb1',
        keywords='pin header, male header',
        min_pads=1,
        max_pads=40,
    )
    generate_cmp(
        dirpath='out/connectors/cmp',
        name='Pin Socket',
        name_lower='female pin socket',
        kind='pinsocket',
        cmpcat='ade6d8ff-3c4f-4dac-a939-cc540c87c280',
        keywords='pin socket, female header',
        min_pads=1,
        max_pads=40,
    )
    generate_pkg(
        dirpath='out/connectors/pkg',
        name='Pin Socket 2.54mm',
        name_lower='female pin socket',
        kind='pinsocket',
        pkgcat='6183d171-e810-475a-a568-2a270aff8f5e',
        keywords='pin socket, female header, tht',
        min_pads=1,
        max_pads=40,
        top_offset=1.5,
        generate_silkscreen=generate_silkscreen_female,
    )
    generate_pkg(
        dirpath='out/connectors/pkg',
        name='Pin Header 2.54mm',
        name_lower='male pin header',
        kind='pinheader',
        pkgcat='e4d3a6bf-af32-48a2-b427-5e794bed949a',
        keywords='pin header, male header, tht',
        min_pads=1,
        max_pads=40,
        top_offset=1.27,
        generate_silkscreen=generate_silkscreen_male,
    )
    generate_pkg(
        dirpath='out/connectors/pkg',
        name='Soldered Wire Connector',
        name_lower='soldered wire connecto',
        kind='wireconnector',
        pkgcat='56a5773f-eeb4-4b39-8cb9-274f3da26f4f',
        keywords='generic connector, soldered wire connector, tht',
        min_pads=1,
        max_pads=10,
        top_offset=1.5,
        generate_silkscreen=generate_silkscreen_female,
    )
    common.save_cache(uuid_cache_file, uuid_cache)
