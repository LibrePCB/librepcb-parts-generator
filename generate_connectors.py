"""
Generate generic connector packages.

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
from uuid import uuid4

pkgcat = '31d0f1d4-a7cc-4792-8b91-21c897fe855f'
min_pads = 1
max_pads = 40
width = 2.54
top = 1.5
spacing = 2.54
pad_drill = 0.8
pad_size = (2.54, 1.27)
line_width = 0.25


def now() -> str:
    return datetime.utcnow().isoformat() + 'Z'


def uuid() -> str:
    return str(uuid4())


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


def generate(dirpath: str):
    for i in range(min_pads, max_pads + 1):
        lines = []

        pkg_uuid = uuid()

        lines.append('(librepcb_package {}'.format(pkg_uuid))
        lines.append(' (name "Generic {}mm 1x{} Connector")'.format(spacing, i))
        lines.append(' (description "A generic connector (1x{}) with {}mm pin spacing.")'.format(
            i, spacing,
        ))
        lines.append(' (keywords "connector, 1x{}")'.format(i))
        lines.append(' (author "LibrePCB")')
        lines.append(' (version "0.1")')
        lines.append(' (created {})'.format(now()))
        lines.append(' (deprecated false)')
        lines.append(' (category {})'.format(pkgcat))
        pad_uuids = [uuid() for _ in range(i)]
        for j in range(1, i + 1):
            lines.append(' (pad {} (name "{}"))'.format(pad_uuids[j - 1], j))
        lines.append(' (footprint {}'.format(uuid()))
        lines.append('  (name "default")')
        lines.append('  (description "")')
        for j in range(1, i + 1):
            y = get_y(j, i, spacing)
            lines.append('  (pad {} (side tht) (shape round)'.format(pad_uuids[j - 1]))
            lines.append('   (pos 0.0 {}) (rot 0.0) (size {} {}) (drill {})'.format(
                y, pad_size[0], pad_size[1], pad_drill,
            ))
            lines.append('  )')

        lines.append('  (polygon {} (layer top_placement)'.format(uuid()))
        lines.append('   (width {}) (fill false) (grab true)'.format(line_width))
        height = get_rectangle_height(i, spacing, top)
        lines.append('   (vertex (pos -1.27 {}) (angle 0.0))'.format(height))
        lines.append('   (vertex (pos 1.27 {}) (angle 0.0))'.format(height))
        lines.append('   (vertex (pos 1.27 -{}) (angle 0.0))'.format(height))
        lines.append('   (vertex (pos -1.27 -{}) (angle 0.0))'.format(height))
        lines.append('   (vertex (pos -1.27 {}) (angle 0.0))'.format(height))
        lines.append('  )')
        if i > 2:  # If there are more than 2 pins, mark pin 1
            lines.append('  (polygon {} (layer top_placement)'.format(uuid()))
            lines.append('   (width {}) (fill false) (grab true)'.format(line_width))
            y_pin0_marker = height - spacing / 2 - top
            lines.append('   (vertex (pos -1.27 -{}) (angle 0.0))'.format(y_pin0_marker))
            lines.append('   (vertex (pos 1.27 -{}) (angle 0.0))'.format(y_pin0_marker))
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


if __name__ == '__main__':
    def _make(dirpath: str):
        if not (path.exists(dirpath) and path.isdir(dirpath)):
            makedirs(dirpath)
    _make('out')
    _make('out/connectors')
    _make('out/connectors/pkg')
    generate('out/connectors/pkg')
