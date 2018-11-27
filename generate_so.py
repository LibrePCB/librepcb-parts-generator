"""
Generate the following SO packages:

- SOIC (both EIAJ and JEDEC)

"""
from os import path, makedirs
from typing import Tuple, Iterable, Optional
from uuid import uuid4

from common import now, init_cache, save_cache
from common import format_float as ff, format_ipc_dimension as fd


generator = 'librepcb-parts-generator (generate_so.py)'

line_width = 0.25
pkg_text_height = 1.0
silkscreen_offset = 0.15
pin_package_offset = 0.762  # Distance between pad center and the package outline


# Initialize UUID cache
uuid_cache_file = 'uuid_cache_so.csv'
uuid_cache = init_cache(uuid_cache_file)


def uuid(category: str, full_name: str, identifier: str) -> str:
    """
    Return a uuid for the specified pin.

    Params:
        category:
            For example 'cmp' or 'pkg'.
        full_name:
            For example "SOIC127P762X120-16".
        identifier:
            For example 'pad-1' or 'pin-13'.
    """
    key = '{}-{}-{}'.format(category, full_name, identifier).lower().replace(' ', '~')
    if key not in uuid_cache:
        uuid_cache[key] = str(uuid4())
    return uuid_cache[key]


def get_y(pin_number: int, pin_count: int, spacing: float, grid_align: bool):
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
    description: str,
    pitch: float,
    pins: Iterable[int],
    heights: Iterable[float],
    body_width: float,
    total_width: float,
    lead_width: float,
    lead_length: float,
    lead_contact_length: float,
    pkgcat: str,
    keywords: str,
    top_offset: float,
    create_date: Optional[str],
):
    category = 'pkg'
    for height in heights:
        for pin_count in pins:
            lines = []

            full_name = name.format(height=fd(height), pin_count=pin_count)
            full_description = description.format(height=height, pin_count=pin_count)

            def _uuid(identifier):
                return uuid(category, full_name, identifier)

            uuid_pkg = _uuid('pkg')
            uuid_pads = [_uuid('pad-{}'.format(p)) for p in range(1, pin_count + 1)]
            uuid_leads = [_uuid('lead-{}'.format(p)) for p in range(1, pin_count + 1)]

            print('Generating {}: {}'.format(full_name, uuid_pkg))

            # General info
            lines.append('(librepcb_package {}'.format(uuid_pkg))
            lines.append(' (name "{}")'.format(full_name))
            lines.append(' (description "{}\\n\\nGenerated with {}")'.format(full_description, generator))
            lines.append(' (keywords "soic{},so{},{}")'.format(pin_count, pin_count, keywords))
            lines.append(' (author "{}")'.format(author))
            lines.append(' (version "0.1")')
            lines.append(' (created {})'.format(create_date or now()))
            lines.append(' (deprecated false)')
            lines.append(' (category {})'.format(pkgcat))
            for p in range(1, pin_count + 1):
                lines.append(' (pad {} (name "{}"))'.format(uuid_pads[p - 1], p))

            def add_footprint_variant(key: str, name: str, pad_width: float, pad_extension: float):
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
                pad_x_offset = total_width / 2 - lead_contact_length / 2 + 0.15 + pad_extension / 2
                for p in range(1, pin_count + 1):
                    mid = pin_count // 2
                    if p <= mid:
                        y = get_y(p, pin_count // 2, pitch, False)
                        pxo = ff(-pad_x_offset)
                    else:
                        y = -get_y(p - mid, pin_count // 2, pitch, False)
                        pxo = ff(pad_x_offset)
                    pad_uuid = uuid_pads[p - 1]
                    lines.append('  (pad {} (side top) (shape rect)'.format(pad_uuid))
                    lines.append('   (position {} {}) (rotation 0.0) (size {} {}) (drill 0.0)'.format(
                        pxo, ff(y), ff(lead_contact_length + 0.15 + pad_extension), pad_width,
                    ))
                    lines.append('  )')

                # Documentation: Leads
                lead_x_offset = body_width / 2
                for p in range(1, pin_count + 1):
                    mid = pin_count // 2
                    if p <= mid:
                        y = get_y(p, pin_count // 2, pitch, False)
                        lxo_min = ff(-lead_x_offset - line_width / 2)
                        lxo_max = ff(-lead_x_offset - line_width / 2 - lead_length)
                    else:
                        y = -get_y(p - mid, pin_count // 2, pitch, False)
                        lxo_min = ff(lead_x_offset + line_width / 2)
                        lxo_max = ff(lead_x_offset + line_width / 2 + lead_length)
                    y_max = ff(y + lead_width / 2)
                    y_min = ff(y - lead_width / 2)
                    lead_uuid = uuid_leads[p - 1]
                    lines.append('  (polygon {} (layer top_documentation)'.format(lead_uuid))
                    lines.append('   (width 0.0) (fill true) (grab_area false)')
                    lines.append('   (vertex (position {} {}) (angle 0.0))'.format(lxo_min, y_max))
                    lines.append('   (vertex (position {} {}) (angle 0.0))'.format(lxo_max, y_max))
                    lines.append('   (vertex (position {} {}) (angle 0.0))'.format(lxo_max, y_min))
                    lines.append('   (vertex (position {} {}) (angle 0.0))'.format(lxo_min, y_min))
                    lines.append('   (vertex (position {} {}) (angle 0.0))'.format(lxo_min, y_max))
                    lines.append('  )')

                # Silkscreen and Documentation
                outline_x_offset = body_width / 2
                bounds = get_rectangle_bounds(pin_count // 2, pitch, top_offset, False)
                for (layer, uuid) in [
                    ('top_placement', uuid_silkscreen),
                    ('top_documentation', uuid_outline),
                ]:
                    lines.append('  (polygon {} (layer {})'.format(uuid, layer))
                    grab = 'true' if layer == 'top_documentation' else 'false'
                    lines.append('   (width {}) (fill false) (grab_area {})'.format(line_width, grab))
                    y_max = ff(bounds[0])
                    y_min = ff(bounds[1])
                    oxo = ff(outline_x_offset)  # Used for shorter lines below :)
                    lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(oxo, y_max))
                    lines.append('   (vertex (position {} {}) (angle 0.0))'.format(oxo, y_max))
                    lines.append('   (vertex (position {} {}) (angle 0.0))'.format(oxo, y_min))
                    lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(oxo, y_min))
                    lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(oxo, y_max))
                    lines.append('  )')

                # Silkscreen: Pin 1 dot
                pin1_dot_diameter = pitch / 2
                lines.append('  (circle {} (layer top_placement)'.format(uuid_pin1_dot))
                lines.append('   (width 0.0) (fill true) (grab_area false) '
                    '(diameter {}) (position -{} {})'.format(
                        ff(pin1_dot_diameter),
                        ff(outline_x_offset - pin1_dot_diameter * 1.5),
                        ff(get_y(1, pin_count // 2, pitch, False)),
                    )
                )
                lines.append('  )')

                # Labels
                bounds = get_rectangle_bounds(pin_count // 2, pitch, top_offset + 1.27, False)
                y_max = ff(bounds[0])
                y_min = ff(bounds[1])
                text_attrs = '(height {}) (stroke_width 0.2) ' \
                             '(letter_spacing auto) (line_spacing auto)'.format(pkg_text_height)
                lines.append('  (stroke_text {} (layer top_names)'.format(uuid_text_name))
                lines.append('   {}'.format(text_attrs))
                lines.append('   (align center bottom) (position 0.0 {}) (rotation 0.0)'.format(y_max))
                lines.append('   (auto_rotate true) (mirror false) (value "{{NAME}}")')
                lines.append('  )')
                lines.append('  (stroke_text {} (layer top_values)'.format(uuid_text_value))
                lines.append('   {}'.format(text_attrs))
                lines.append('   (align center top) (position 0.0 {}) (rotation 0.0)'.format(y_min))
                lines.append('   (auto_rotate true) (mirror false) (value "{{VALUE}}")')
                lines.append('  )')

                lines.append(' )')

            add_footprint_variant('reflow', 'reflow', 0.6, 0.0)
            add_footprint_variant('handsoldering', 'hand soldering', 0.7, 0.5)

            lines.append(')')

            pkg_dir_path = path.join(dirpath, uuid_pkg)
            if not (path.exists(pkg_dir_path) and path.isdir(pkg_dir_path)):
                makedirs(pkg_dir_path)
            with open(path.join(pkg_dir_path, '.librepcb-pkg'), 'w') as f:
                f.write('0.1\n')
            with open(path.join(pkg_dir_path, 'package.lp'), 'w') as f:
                f.write('\n'.join(lines))
                f.write('\n')


if __name__ == '__main__':
    def _make(dirpath: str):
        if not (path.exists(dirpath) and path.isdir(dirpath)):
            makedirs(dirpath)
    _make('out')
    _make('out/soic')
    _make('out/soic/pkg')
    generate_pkg(
        dirpath='out/soic/pkg',
        author='Danilo B.',
        name='SOIC127P762X{height}-{pin_count}',
        description='{pin_count}-pin Small Outline Integrated Circuit (SOIC), '
                    'standardized by EIAJ.\\n\\n'
                    'Pitch: 1.27 mm\\nNominal width: 7.62mm\\nHeight: {height:.2f}mm',
        pitch=1.27,
        pins=[6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 28, 30, 32],
        heights=[1.2, 1.4, 1.7, 2.7],
        body_width=5.22,
        total_width=8.42,
        lead_width=0.4,
        lead_length=1.6,
        lead_contact_length=0.8,
        pkgcat='a074fabf-4912-4c29-bc6b-451bf43c2193',
        keywords='so,soic,small outline,smd,eiaj',
        top_offset=1.0,
        create_date='2018-11-10T20:32:03Z',
    )
    generate_pkg(
        dirpath='out/soic/pkg',
        author='Danilo B.',
        name='SOIC127P1524X{height}-{pin_count}',
        description='{pin_count}-pin Small Outline Integrated Circuit (SOIC), '
                    'standardized by EIAJ.\\n\\n'
                    'Pitch: 1.27 mm\\nNominal width: 15.24mm\\nHeight: {height:.2f}mm',
        pitch=1.27,
        pins=[20, 22, 24, 28, 30, 32, 36, 40, 42, 44],
        heights=[1.2, 1.4, 1.7, 2.7],
        body_width=12.84,
        total_width=16.04,
        lead_width=0.4,
        lead_length=1.6,
        lead_contact_length=0.8,
        pkgcat='a074fabf-4912-4c29-bc6b-451bf43c2193',
        keywords='so,soic,small outline,smd,eiaj',
        top_offset=1.0,
        create_date='2018-11-10T20:32:03Z',
    )
    generate_pkg(
        dirpath='out/soic/pkg',
        author='Danilo B.',
        name='SOIC127P600X{height}-{pin_count}',
        description='{pin_count}-pin Small Outline Integrated Circuit (SOIC), '
                    'standardized by JEDEC.\\n\\n'
                    'Pitch: 1.27 mm\\nNominal width: 6.00mm\\nHeight: {height:.2f}mm',
        pitch=1.27,
        pins=[6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 28, 30, 32, 36, 40, 42, 44, 48],
        heights=[1.75],
        body_width=3.9,
        total_width=6.0,
        lead_width=0.45,
        lead_length=1.04,
        lead_contact_length=0.835,
        pkgcat='a074fabf-4912-4c29-bc6b-451bf43c2193',
        keywords='so,soic,small outline,smd,jedec',
        top_offset=0.8,
        create_date='2018-11-10T20:32:03Z',
    )
    save_cache(uuid_cache_file, uuid_cache)
