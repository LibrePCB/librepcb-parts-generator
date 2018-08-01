"""
Generate pin header and socket strip packages.

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
from typing import Callable, List
from uuid import uuid4

import common

generator = 'librepcb-parts-generator (generate_connectors.py)'

min_pads = 1
max_pads = 40
width = 2.54
top = 1.5
spacing = 2.54
pad_drill = 1.0
pad_size = (2.54, 1.27)
line_width = 0.25


# Initialize UUID cache
uuid_cache_file = 'uuid_cache_connectors.csv'
uuid_cache = common.init_cache(uuid_cache_file)


def now() -> str:
    return datetime.utcnow().isoformat() + 'Z'


def uuid(kind: str, typ: str, pin_number: int, identifier: str = None) -> str:
    if identifier:
        key = '{}-{}-1x{}-{}'.format(kind, typ, pin_number, identifier).lower().replace(' ', '~')
    else:
        key = '{}-{}-1x{}'.format(kind, typ, pin_number).lower().replace(' ', '~')
    if key not in uuid_cache:
        uuid_cache[key] = str(uuid4())
    return uuid_cache[key]


def get_y(pin_number: int, pin_count: int, spacing: float):
    """
    Return the y coordinate of the specified pin.

    The pin number is 1 index based.

    """
    mid = (pin_count + 1) // 2
    even = pin_count % 2 == 0
    offset = spacing / 2 if even else 0
    return round(pin_number * spacing - mid * spacing - offset, 2)


def get_rectangle_height(pin_count: int, spacing: float, top: float):
    """
    Return the y height of the rectangle around the pins.
    """
    return (pin_count - 1) / 2 * spacing + top


def generate(
    dirpath: str,
    name: str,
    name_lower: str,
    kind: str,
    pkgcat: str,
    keywords: str,
    generate_silkscreen: Callable[[List[str], str, int], None]
):
    for i in range(min_pads, max_pads + 1):
        lines = []

        pkg_uuid = uuid(kind, 'pkg', i)

        lines.append('(librepcb_package {}'.format(pkg_uuid))
        lines.append(' (name "{} {}mm 1x{}")'.format(name, spacing, i))
        lines.append(' (description "A 1x{} {} with {}mm pin spacing.\\n\\n'
                     'Generated with {}")'.format(name_lower, i, spacing, generator))
        lines.append(' (keywords "connector, 1x{}, {}")'.format(i, keywords))
        lines.append(' (author "LibrePCB")')
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
        for j in range(1, i + 1):
            y = get_y(j, i, spacing)
            lines.append('  (pad {} (side tht) (shape round)'.format(pad_uuids[j - 1]))
            lines.append('   (pos 0.0 {}) (rot 0.0) (size {} {}) (drill {})'.format(
                y, pad_size[0], pad_size[1], pad_drill,
            ))
            lines.append('  )')

        generate_silkscreen(lines, kind, i)

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


def generate_silkscreen_female(lines: List[str], kind: str, pins: int) -> None:
    lines.append('  (polygon {} (layer top_placement)'.format(
        uuid(kind, 'polygon', pins, 'contour'))
    )
    lines.append('   (width {}) (fill false) (grab true)'.format(line_width))
    height = get_rectangle_height(pins, spacing, top)
    lines.append('   (vertex (pos -1.27 {}) (angle 0.0))'.format(height))
    lines.append('   (vertex (pos 1.27 {}) (angle 0.0))'.format(height))
    lines.append('   (vertex (pos 1.27 -{}) (angle 0.0))'.format(height))
    lines.append('   (vertex (pos -1.27 -{}) (angle 0.0))'.format(height))
    lines.append('   (vertex (pos -1.27 {}) (angle 0.0))'.format(height))
    lines.append('  )')
    if pins > 2:  # If there are more than 2 pins, mark pin 1
        lines.append('  (polygon {} (layer top_placement)'.format(
            uuid(kind, 'polygon', pins, 'pin1mark'),
        ))
        lines.append('   (width {}) (fill false) (grab true)'.format(line_width))
        y_pin0_marker = height - spacing / 2 - top
        lines.append('   (vertex (pos -1.27 -{}) (angle 0.0))'.format(y_pin0_marker))
        lines.append('   (vertex (pos 1.27 -{}) (angle 0.0))'.format(y_pin0_marker))
        lines.append('  )')


def generate_silkscreen_male(lines: List[str], kind: str, pins: int) -> None:
    pass


if __name__ == '__main__':
    def _make(dirpath: str):
        if not (path.exists(dirpath) and path.isdir(dirpath)):
            makedirs(dirpath)
    _make('out')
    _make('out/connectors')
    _make('out/connectors/pkg')
    generate(
        dirpath='out/connectors/pkg',
        name='Socket Strip',
        name_lower='female socket strip',
        kind='socketstrip',
        pkgcat='3fe529fe-b8b1-489b-beae-da54e01c9b20',
        keywords='socket strip, female header, tht',
        generate_silkscreen=generate_silkscreen_female,
    )
    generate(
        dirpath='out/connectors/pkg',
        name='Pin Header',
        name_lower='male pin header',
        kind='pinheader',
        pkgcat='f8be0636-474e-41ea-8340-05caf137596c',
        keywords='pin header, male header, tht',
        generate_silkscreen=generate_silkscreen_male,
    )
    common.save_cache(uuid_cache_file, uuid_cache)
