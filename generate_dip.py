"""
Generate DIP packages.
"""
from os import makedirs, path
from uuid import uuid4

from typing import Iterable, Optional, Tuple

from common import format_float as ff
from common import init_cache, now, save_cache

generator = 'librepcb-parts-generator (generate_dip.py)'

spacing = 2.54
line_width = 0.25
drill_diameter = 0.8
pkg_text_height = 1.0
silkscreen_offset = 0.15
pin_package_offset = 0.762  # Distance between drill hole and the package outline


# Initialize UUID cache
uuid_cache_file = 'uuid_cache_dip.csv'
uuid_cache = init_cache(uuid_cache_file)


def uuid(category: str, width: str, variant: str, identifier: str) -> str:
    """
    Return a uuid for the specified pin.

    Params:
        category:
            For example 'cmp' or 'pkg'.
        width:
            For example "7.62" or "15.24".
        variant:
            For example '8' or '28'.
        identifier:
            For example 'pad-1' or 'pin-13'.
    """
    key = '{}-{}-{}-{}'.format(category, width, variant, identifier).lower().replace(' ', '~')
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
    width: str,
    pkgcat: str,
    keywords: str,
    pins: Iterable[int],
    top_offset: float,
    create_date: Optional[str],
) -> None:
    category = 'pkg'
    for pin_count in pins:
        lines = []

        variant = '{}pin-D{:.1f}'.format(pin_count, drill_diameter)

        def _uuid(identifier: str) -> str:
            return uuid(category, width, variant, identifier)

        uuid_pkg = _uuid('pkg')
        uuid_pads = [_uuid('pad-{}'.format(p)) for p in range(1, pin_count + 1)]

        # General info
        lines.append('(librepcb_package {}'.format(uuid_pkg))
        lines.append(' (name "{}-{} {}mm")'.format(name, pin_count, width))
        lines.append(' (description "{}-lead {}mm wide {}\\n\\n'
                     'Generated with {}")'.format(pin_count, width, name_lower, generator))
        lines.append(' (keywords "dip{},pdip{},{}")'.format(pin_count, pin_count, keywords))
        lines.append(' (author "{}")'.format(author))
        lines.append(' (version "0.1")')
        lines.append(' (created {})'.format(create_date or now()))
        lines.append(' (deprecated false)')
        lines.append(' (category {})'.format(pkgcat))
        for p in range(1, pin_count + 1):
            lines.append(' (pad {} (name "{}"))'.format(uuid_pads[p - 1], p))

        def add_footprint_variant(key: str, name: str, pad_size: Tuple[float, float]) -> None:
            uuid_footprint = _uuid('footprint-{}'.format(key))
            uuid_silkscreen = _uuid('polygon-silkscreen-{}'.format(key))
            uuid_pin1_dot = _uuid('pin1-dot-silkscreen-{}'.format(key))
            uuid_outline = _uuid('polygon-outline-{}'.format(key))
            uuid_text_name = _uuid('text-name-{}'.format(key))
            uuid_text_value = _uuid('text-value-{}'.format(key))

            lines.append(' (footprint {}'.format(uuid_footprint))
            lines.append('  (name "{}")'.format(name))
            lines.append('  (description "")')

            # Pads
            pad_x_offset = float(width) / 2
            for p in range(1, pin_count // 2 + 1):
                # Down on the left
                y = get_y(p, pin_count // 2, spacing, False)
                shape = 'rect' if p == 1 else 'round'
                pad_uuid = uuid_pads[p - 1]
                lines.append('  (pad {} (side tht) (shape {})'.format(pad_uuid, shape))
                lines.append('   (position {} {}) (rotation 0.0) (size {} {}) (drill {})'.format(
                    ff(-pad_x_offset), ff(y), pad_size[0], pad_size[1], drill_diameter,
                ))
                lines.append('  )')
            for p in range(1, pin_count // 2 + 1):
                # Up on the right
                y = -get_y(p, pin_count // 2, spacing, False)
                shape = 'round'
                pad_uuid = uuid_pads[p + pin_count // 2 - 1]
                lines.append('  (pad {} (side tht) (shape {})'.format(pad_uuid, shape))
                lines.append('   (position {} {}) (rotation 0.0) (size {} {}) (drill {})'.format(
                    ff(pad_x_offset), ff(y), pad_size[0], pad_size[1], drill_diameter,
                ))
                lines.append('  )')

            # Silkscreen: Rectangle
            lines.append('  (polygon {} (layer top_placement)'.format(uuid_silkscreen))
            lines.append('   (width {}) (fill false) (grab_area false)'.format(line_width))
            y_max, y_min = get_rectangle_bounds(pin_count // 2, spacing, top_offset, False)
            silkscreen_x_offset = pad_x_offset - pad_size[0] / 2 \
                - silkscreen_offset - line_width / 2
            sxo = ff(silkscreen_x_offset)  # Used for shorter lines below :)
            lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(sxo, ff(y_max)))  # NW
            lines.append('   (vertex (position -{} {}) (angle 180.0))'.format(
                ff(silkscreen_x_offset / 3), ff(y_max),
            ))
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(
                ff(silkscreen_x_offset / 3), ff(y_max),
            ))
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(sxo, ff(y_max)))  # NE
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(sxo, ff(y_min)))  # SE
            lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(sxo, ff(y_min)))  # SW
            lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(sxo, ff(y_max)))  # NW
            lines.append('  )')

            # Documentation
            # TODO: The code below is almost identical to the silkscreen, code could be reused
            lines.append('  (polygon {} (layer top_documentation)'.format(uuid_outline))
            lines.append('   (width {}) (fill false) (grab_area true)'.format(line_width))
            y_max, y_min = get_rectangle_bounds(pin_count // 2, spacing, top_offset, False)
            outline_x_offset = pad_x_offset - pin_package_offset
            oxo = ff(outline_x_offset)  # Used for shorter lines below :)
            lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(oxo, ff(y_max)))
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(oxo, ff(y_max)))
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(oxo, ff(y_min)))
            lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(oxo, ff(y_min)))
            lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(oxo, ff(y_max)))
            lines.append('  )')

            # Silkscreen: Pin 1 dot
            pin1_dot_diameter = float(width) / 7.62
            lines.append('  (circle {} (layer top_placement)'.format(uuid_pin1_dot))
            lines.append('   (width 0.0) (fill true) (grab_area false) '
                         '(diameter {}) (position -{} {})'.format(
                             ff(pin1_dot_diameter),
                             ff(silkscreen_x_offset - pin1_dot_diameter),
                             ff(y_max - pin1_dot_diameter),
                         ))
            lines.append('  )')

            # Labels
            y_max, y_min = get_rectangle_bounds(pin_count // 2, spacing, top_offset + 1.27, False)
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

        add_footprint_variant('handsoldering', 'hand soldering', (2.54, 1.27))
        add_footprint_variant('compact', 'compact', (1.6, 1.6))

        lines.append(')')

        pkg_dir_path = path.join(dirpath, uuid_pkg)
        if not (path.exists(pkg_dir_path) and path.isdir(pkg_dir_path)):
            makedirs(pkg_dir_path)
        with open(path.join(pkg_dir_path, '.librepcb-pkg'), 'w') as f:
            f.write('0.1\n')
        with open(path.join(pkg_dir_path, 'package.lp'), 'w') as f:
            f.write('\n'.join(lines))
            f.write('\n')

        print('{}pin {}mm DIP: Wrote package {}'.format(pin_count, width, uuid_pkg))


if __name__ == '__main__':
    def _make(dirpath: str) -> None:
        if not (path.exists(dirpath) and path.isdir(dirpath)):
            makedirs(dirpath)
    _make('out')
    _make('out/dip')
    _make('out/dip/pkg')
    generate_pkg(
        dirpath='out/dip/pkg',
        author='Danilo B.',
        name='DIP',
        name_lower='Dual Inline Package',
        width='7.62',
        pkgcat='edc63ee6-ea87-495d-a6b9-54536fe8b1f9',
        keywords='dip,pdip,cdip,cerdip,dual inline package',
        pins=[4, 6, 8, 14, 16, 18, 20, 24, 28],
        top_offset=0.8255,
        create_date='2018-11-04T23:13:00Z',
    )
    generate_pkg(
        dirpath='out/dip/pkg',
        author='Danilo B.',
        name='DIP',
        name_lower='Dual Inline Package',
        width='15.24',
        pkgcat='edc63ee6-ea87-495d-a6b9-54536fe8b1f9',
        keywords='dip,pdip,cdip,cerdip,dual inline package,wide',
        pins=[24, 28, 32, 36, 40, 48, 52, 64],
        top_offset=0.8255,
        create_date='2018-11-04T23:13:00Z',
    )
    save_cache(uuid_cache_file, uuid_cache)
