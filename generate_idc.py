"""
Generate IDC style packages.

Implemented so far:

- CNC Tech 3020-xx-0300-00 (2.54 mm pitch)
- CNC Tech 3120-xx-0300-00 (2.00 mm pitch)
- CNC Tech 3220-xx-0300-00 (1.27 mm pitch)

"""
from math import sqrt
from os import makedirs, path
from uuid import uuid4

from typing import Iterable, Tuple

from common import format_float as ff
from common import init_cache, save_cache

generator = 'librepcb-parts-generator (generate_idc.py)'

# Global constants
line_width = 0.25
silkscreen_offset = 0.150  # 150 µm
courtyard_offset = 0.25
pkg_text_height = 1.0
sym_text_height = 2.54

# Initialize UUID cache
uuid_cache_file = 'uuid_cache_idc.csv'
uuid_cache = init_cache(uuid_cache_file)


def uuid(category: str, kind: str, variant: str, identifier: str) -> str:
    """
    Return a uuid for the specified object.

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


class Coord:
    def __init__(self, x: float, y: float, round_values: bool = True):
        if x == -0.0:
            x = 0.0
        if y == -0.0:
            y = 0.0
        if round_values:
            self.x = round(x, 2)
            self.y = round(y, 2)
        else:
            self.x = x
            self.y = y


def get_coords(pin_number: int, pin_count: int, row_count: int, pitch: float, row_spacing: float) -> Coord:
    """
    Return the x/y coordinates of the specified pin.

    The pin number is 1 index based. Pin 1 is at the top left. Pins are
    numbered horizontally, wrapping around.

    Example for 2 rows:

      1 2
      3 4
      5 6

    Example for 3 rows:

      1 2 3
      4 5 6
      7 8 9

    """
    assert pin_count % row_count == 0
    lines = pin_count // row_count

    # For 3 rows, this will be either 0, 1 or 2
    xpos = (pin_number - 1) % row_count
    # Determine x position
    x = xpos * row_spacing - (row_count - 1) * row_spacing / 2

    # For 2 columns and 8 pins, this will be either 0, 1, 2 or 3
    ypos = ((pin_number - 1) // row_count) % (pin_count / row_count)
    # Determine y position
    y = -ypos * pitch + (lines - 1) * pitch / 2

    return Coord(x, y)


def generate_pkg(
    dirpath: str,
    author: str,
    name: str,
    description: str,
    pins: Iterable[int],
    pitch: float,
    row_spacing: float,
    pad_size: Tuple[float, float],  # (x, y)
    pad_x_offset: float,  # positive = move out, negative = move in
    body_offset_x: float,
    body_offset_y: float,
    body_gap: float,
    lead_width: float,
    lead_span: float,
    pkgcats: Iterable[str],
    keywords: str,
    version: str,
    create_date: str,
) -> None:
    category = 'pkg'
    for pin_count in pins:
        lines = []

        formatted_name = name.format(pin_count=str(pin_count).rjust(2, '0'))
        formatted_desc = description.format(pin_count=pin_count)

        def _uuid(identifier: str) -> str:
            kind = formatted_name.replace(' ', '-').lower()
            return uuid(category, kind, str(pin_count), identifier)

        uuid_pkg = _uuid('pkg')
        uuid_pads = [_uuid('pad-{}'.format(p)) for p in range(pin_count)]
        uuid_leads = [_uuid('lead-{}'.format(p)) for p in range(pin_count)]
        uuid_footprint = _uuid('footprint-default')
        uuid_text_name = _uuid('text-name')
        uuid_text_value = _uuid('text-value')
        uuid_placement_north = _uuid('placement-north')
        uuid_placement_south = _uuid('placement-south')
        uuid_doc_contour = _uuid('documentation-contour')
        uuid_doc_triangle = _uuid('documentation-triangle')
        uuid_grab_area = _uuid('grab-area')
        uuid_courtyard = _uuid('courtyard')

        # General info
        lines.append('(librepcb_package {}'.format(uuid_pkg))
        lines.append(' (name "{}")'.format(formatted_name))
        lines.append(' (description "{}\\n\\nGenerated with {}")'.format(formatted_desc, generator))
        lines.append(' (keywords "{}")'.format(keywords))
        lines.append(' (author "{}")'.format(author))
        lines.append(' (version "{}")'.format(version))
        lines.append(' (created {})'.format(create_date))
        lines.append(' (deprecated false)')
        for pkgcat in sorted(pkgcats):
            lines.append(' (category {})'.format(pkgcat))
        for j in range(1, pin_count + 1):
            lines.append(' (pad {} (name "{}"))'.format(uuid_pads[j - 1], j))
        lines.append(' (footprint {}'.format(uuid_footprint))
        lines.append('  (name "default")')
        lines.append('  (description "")')

        # Pads
        for i in range(1, pin_count + 1):
            coords = get_coords(i, pin_count, 2, pitch, row_spacing)
            x_offset_abs = pad_size[0] / 2 + pad_x_offset
            x_offset = -x_offset_abs if i % 2 == 1 else x_offset_abs
            lines.append('  (pad {} (side top) (shape rect)'.format(uuid_pads[i - 1]))
            lines.append('   (position {} {}) (rotation 0.0) (size {} {}) (drill 0.0)'.format(
                ff(coords.x + x_offset), ff(coords.y),
                ff(pad_size[0]), ff(pad_size[1]),
            ))
            lines.append('  )')

        vertex = '   (vertex (position {} {}) (angle 0.0))'

        # Legs on documentation layer
        for i in range(1, pin_count + 1):
            coords = get_coords(i, pin_count, 2, pitch, row_spacing)
            x_offset_abs = pad_size[0] / 2 + pad_x_offset
            x_offset = -x_offset_abs if i % 2 == 1 else x_offset_abs
            sign = 1 if coords.x > 0 else -1
            lines.append('  (polygon {} (layer top_documentation)'.format(uuid_leads[i - 1]))
            lines.append('   (width 0.0) (fill true) (grab_area false)')
            lines.append(vertex.format(ff(coords.x - lead_width / 2 * sign), ff(coords.y + lead_width / 2)))
            lines.append(vertex.format(ff(coords.x - lead_width / 2 * sign), ff(coords.y - lead_width / 2)))
            lines.append(vertex.format(ff(lead_span / 2 * sign), ff(coords.y - lead_width / 2)))
            lines.append(vertex.format(ff(lead_span / 2 * sign), ff(coords.y + lead_width / 2)))
            lines.append(vertex.format(ff(coords.x - lead_width / 2 * sign), ff(coords.y + lead_width / 2)))
            lines.append('  )')

        # Body bounds
        pin1 = get_coords(1, pin_count, 2, pitch, row_spacing)
        body_bounds = (
            abs(pin1.x) + body_offset_x,
            abs(pin1.y) + body_offset_y,
        )
        x_inside_body = body_bounds[0] - line_width / 2
        x_outside_body = body_bounds[0] + line_width / 2
        y_inside_body = body_bounds[1] - line_width / 2
        y_outside_body = body_bounds[1] + line_width / 2

        # Silkscreen
        x_mark_pin1 = abs(pin1.x) + pad_size[0] + pad_x_offset - line_width / 2
        y_above_pin1 = pin1.y + pad_size[1] / 2 + silkscreen_offset + line_width / 2
        # North part contains extended line to mark pin 1
        lines.append('  (polygon {} (layer top_placement)'.format(uuid_placement_north))
        lines.append('   (width {}) (fill false) (grab_area false)'.format(line_width))
        lines.append(vertex.format(ff(-x_mark_pin1), ff(y_above_pin1)))
        lines.append(vertex.format(ff(-x_outside_body), ff(y_above_pin1)))
        lines.append(vertex.format(ff(-x_outside_body), ff(y_outside_body)))
        lines.append(vertex.format(ff(x_outside_body), ff(y_outside_body)))
        lines.append(vertex.format(ff(x_outside_body), ff(y_above_pin1)))
        lines.append('  )')
        # South part doesn't contain any pin markings
        lines.append('  (polygon {} (layer top_placement)'.format(uuid_placement_south))
        lines.append('   (width {}) (fill false) (grab_area false)'.format(line_width))
        lines.append(vertex.format(ff(x_outside_body), ff(-y_above_pin1)))
        lines.append(vertex.format(ff(x_outside_body), ff(-y_outside_body)))
        lines.append(vertex.format(ff(-x_outside_body), ff(-y_outside_body)))
        lines.append(vertex.format(ff(-x_outside_body), ff(-y_above_pin1)))
        lines.append('  )')

        # Documentation layer
        lines.append('  (polygon {} (layer top_documentation)'.format(uuid_doc_contour))
        lines.append('   (width {}) (fill false) (grab_area false)'.format(line_width))
        lines.append(vertex.format(ff(-x_inside_body), ff(body_gap / 2)))
        lines.append(vertex.format(ff(-x_inside_body), ff(y_inside_body)))
        lines.append(vertex.format(ff(x_inside_body), ff(y_inside_body)))
        lines.append(vertex.format(ff(x_inside_body), ff(-y_inside_body)))
        lines.append(vertex.format(ff(-x_inside_body), ff(-y_inside_body)))
        lines.append(vertex.format(ff(-x_inside_body), ff(-body_gap / 2)))
        lines.append('  )')

        # Triangle on doc layer
        triangle_size = 1.0
        triangle_width = sqrt(3) / 2.0 * triangle_size * 0.8
        triangle_offset = triangle_size / 2  # Offset from doc layer
        lines.append('  (polygon {} (layer top_documentation)'.format(uuid_doc_triangle))
        lines.append('   (width 0.0) (fill true) (grab_area false)')
        lines.append(vertex.format(ff(-x_inside_body + triangle_offset), ff(y_inside_body - triangle_offset)))
        lines.append(vertex.format(ff(-x_inside_body + triangle_offset), ff(y_inside_body - triangle_offset - triangle_size)))
        lines.append(vertex.format(ff(-x_inside_body + triangle_offset + triangle_width), ff(y_inside_body - triangle_offset - triangle_size / 2)))
        lines.append(vertex.format(ff(-x_inside_body + triangle_offset), ff(y_inside_body - triangle_offset)))
        lines.append('  )')

        # Grab area
        lines.append('  (polygon {} (layer top_hidden_grab_areas)'.format(uuid_grab_area))
        lines.append('   (width 0.0) (fill true) (grab_area true)')
        lines.append(vertex.format(ff(-body_bounds[0]), ff(body_bounds[1])))
        lines.append(vertex.format(ff(body_bounds[0]), ff(body_bounds[1])))
        lines.append(vertex.format(ff(body_bounds[0]), ff(-body_bounds[1])))
        lines.append(vertex.format(ff(-body_bounds[0]), ff(-body_bounds[1])))
        lines.append(vertex.format(ff(-body_bounds[0]), ff(body_bounds[1])))
        lines.append('  )')

        # Courtyard
        x_courtyard = body_bounds[0] + line_width + courtyard_offset
        x_courtyard_extended = abs(pin1.x) + pad_size[0] + pad_x_offset + courtyard_offset
        y_courtyard = body_bounds[1] + line_width + courtyard_offset
        y_courtyard_extended = y_above_pin1 + line_width / 2 + courtyard_offset
        lines.append('  (polygon {} (layer top_courtyard)'.format(uuid_courtyard))
        lines.append('   (width {}) (fill false) (grab_area false)'.format(line_width))
        lines.append(vertex.format(ff(-x_courtyard_extended), ff(y_courtyard_extended)))
        lines.append(vertex.format(ff(-x_courtyard), ff(y_courtyard_extended)))
        lines.append(vertex.format(ff(-x_courtyard), ff(y_courtyard)))
        lines.append(vertex.format(ff(x_courtyard), ff(y_courtyard)))
        lines.append(vertex.format(ff(x_courtyard), ff(y_courtyard_extended)))
        lines.append(vertex.format(ff(x_courtyard_extended), ff(y_courtyard_extended)))
        lines.append(vertex.format(ff(x_courtyard_extended), ff(-y_courtyard_extended)))
        lines.append(vertex.format(ff(x_courtyard), ff(-y_courtyard_extended)))
        lines.append(vertex.format(ff(x_courtyard), ff(-y_courtyard)))
        lines.append(vertex.format(ff(-x_courtyard), ff(-y_courtyard)))
        lines.append(vertex.format(ff(-x_courtyard), ff(-y_courtyard_extended)))
        lines.append(vertex.format(ff(-x_courtyard_extended), ff(-y_courtyard_extended)))
        lines.append(vertex.format(ff(-x_courtyard_extended), ff(y_courtyard_extended)))
        lines.append('  )')

        # Labels
        body_y_max = (pin_count / 2 - 1) * pitch / 2 + body_offset_y
        text_attrs = '(height {}) (stroke_width 0.2) ' \
                     '(letter_spacing auto) (line_spacing auto)'.format(pkg_text_height)
        lines.append('  (stroke_text {} (layer top_names)'.format(uuid_text_name))
        lines.append('   {}'.format(text_attrs))
        lines.append('   (align center bottom) (position 0.0 {}) (rotation 0.0)'.format(
            ff(body_y_max + 1),
        ))
        lines.append('   (auto_rotate true) (mirror false) (value "{{NAME}}")')
        lines.append('  )')
        lines.append('  (stroke_text {} (layer top_values)'.format(uuid_text_value))
        lines.append('   {}'.format(text_attrs))
        lines.append('   (align center top) (position 0.0 {}) (rotation 0.0)'.format(
            ff(-body_y_max - 1),
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

        print('{}x{} {} mm: Wrote package {}'.format(2, pin_count // 2, pitch, uuid_pkg))


if __name__ == '__main__':
    def _make(dirpath: str) -> None:
        if not (path.exists(dirpath) and path.isdir(dirpath)):
            makedirs(dirpath)
    _make('out')
    _make('out/idc')
    _make('out/idc/pkg')
    generate_pkg(
        dirpath='out/idc/pkg',
        author='Danilo Bargen',
        name='CNCTECH_3220-{pin_count}-0300-XX',
        description='{pin_count}-pin 1.27mm pitch SMD IDC box header by CNC Tech.',
        pins=[10, 14, 16, 20, 26, 30, 34, 40, 50, 60],
        pitch=1.27,
        row_spacing=1.27,
        pad_size=(2.4, 0.76),
        pad_x_offset=0.115,
        body_offset_x=1.915,
        body_offset_y=3.785,
        body_gap=2.35,
        lead_width=0.4,
        lead_span=5.5,
        pkgcats=['92186130-e1a4-4a82-8ce9-88f4aa854195', 'e4d3a6bf-af32-48a2-b427-5e794bed949a'],
        keywords='cnc tech,idc,header,male,box header,smd,3220,1.27mm',
        version='0.1',
        create_date='2019-07-09T21:31:21Z',
    )
    generate_pkg(
        dirpath='out/idc/pkg',
        author='Danilo Bargen',
        name='CNCTECH_3120-{pin_count}-0300-XX',
        description='{pin_count}-pin 2.00mm pitch SMD IDC box header by CNC Tech.',
        pins=[6, 8, 10, 12, 14, 16, 18, 20, 24, 26, 30, 34, 40, 44, 50, 60, 64],
        pitch=2.0,
        row_spacing=2.0,
        pad_size=(3.45, 0.9),
        pad_x_offset=-0.2,
        body_offset_x=1.75,
        body_offset_y=4.65,
        body_gap=3.7,
        lead_width=0.5,
        lead_span=7.5,
        pkgcats=['92186130-e1a4-4a82-8ce9-88f4aa854195', 'e4d3a6bf-af32-48a2-b427-5e794bed949a'],
        keywords='cnc tech,idc,header,male,box header,smd,3120,2.00mm',
        version='0.1',
        create_date='2019-07-09T21:31:21Z',
    )
    generate_pkg(
        dirpath='out/idc/pkg',
        author='Danilo Bargen',
        name='CNCTECH_3020-{pin_count}-0300-XX',
        description='{pin_count}-pin 2.54mm pitch SMD IDC box header by CNC Tech.',
        pins=[6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 40, 44, 50, 60, 64],
        pitch=2.54,
        row_spacing=2.54,
        pad_size=(4.8, 0.9),
        pad_x_offset=-0.42,
        body_offset_x=3.13,
        body_offset_y=5.08,
        body_gap=5.08,
        lead_width=0.64,
        lead_span=10.2,
        pkgcats=['92186130-e1a4-4a82-8ce9-88f4aa854195', 'e4d3a6bf-af32-48a2-b427-5e794bed949a'],
        keywords='cnc tech,idc,header,male,box header,smd,3020,2.54mm',
        version='0.1',
        create_date='2019-07-09T21:31:21Z',
    )
    save_cache(uuid_cache_file, uuid_cache)
