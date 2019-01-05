"""
Generate the following packages:

- Chip resistors SMT

"""
from os import path, makedirs
from typing import Iterable, Optional, Dict, Any  # noqa
from uuid import uuid4

from common import now, init_cache, save_cache
from common import format_float as ff, format_ipc_dimension as fd
from common import generate_courtyard, indent


generator = 'librepcb-parts-generator (generate_chip.py)'

line_width = 0.25
line_width_thin = 0.15
line_width_thinner = 0.1
pkg_text_height = 1.0
label_offset = 1.1
label_offset_thin = 0.8
silkscreen_clearance = 0.15
handsoldering_toe_extension = 0.5


# Based on IPC 7351B (Table 3-5)
DENSITY_LEVELS = {  # For 1608 and up
    'A': {'toe': 0.55, 'heel': 0.00, 'side': 0.05, 'courtyard': 0.50},
    'B': {'toe': 0.35, 'heel': 0.00, 'side': 0.00, 'courtyard': 0.25},
    'C': {'toe': 0.15, 'heel': 0.00, 'side': -0.05, 'courtyard': 0.12},
}
# Based on IPC 7351B (Table 3-6)
# Heel has been set to 0.00 instead of -0.05, since IPC 7351C will probably
# use those values too.
DENSITY_LEVELS_SMALL = {  # Below 1608
    'A': {'toe': 0.20, 'heel': 0.00, 'side': 0.05, 'courtyard': 0.20},
    'B': {'toe': 0.10, 'heel': 0.00, 'side': 0.00, 'courtyard': 0.15},
    'C': {'toe': 0.00, 'heel': 0.00, 'side': 0.00, 'courtyard': 0.10},
}


def get_by_density(length: float, level: str, key: str):
    if length >= 1.6:
        table = DENSITY_LEVELS
    else:
        table = DENSITY_LEVELS_SMALL
    return table[level][key]


# Initialize UUID cache
uuid_cache_file = 'uuid_cache_chip.csv'
uuid_cache = init_cache(uuid_cache_file)


def uuid(category: str, full_name: str, identifier: str) -> str:
    """
    Return a uuid for the specified pin.

    Params:
        category:
            For example 'cmp' or 'pkg'.
        full_name:
            For example "RESC3216X65".
        identifier:
            For example 'pad-1' or 'pin-13'.
    """
    key = '{}-{}-{}'.format(category, full_name, identifier).lower().replace(' ', '~')
    if key not in uuid_cache:
        uuid_cache[key] = str(uuid4())
    return uuid_cache[key]


class ChipConfig:
    def __init__(
        self,
        size_imperial: str,  # String, e.g. "1206"
        length: float,
        width: float,
        height: float,
        gap: float,
    ):
        self._size_imperial = size_imperial
        self.length = length
        self.width = width
        self.height = height
        self.gap = gap

    def size_metric(self) -> str:
        return str(int(self.length * 10)).rjust(2, '0') + str(int(self.width * 10)).rjust(2, '0')

    def size_imperial(self) -> str:
        return self._size_imperial


def generate_pkg(
    dirpath: str,
    author: str,
    name: str,
    description: str,
    configs: Iterable[ChipConfig],
    pkgcat: str,
    keywords: str,
    create_date: Optional[str],
):
    category = 'pkg'
    for config in configs:
        lines = []

        fmt_params = {
            'size_metric': config.size_metric(),
            'size_imperial': config.size_imperial(),
        }  # type: Dict[str, Any]
        fmt_params_name = {
            **fmt_params,
            'height': fd(config.height),
        }
        fmt_params_desc = {
            **fmt_params,
            'length': config.length,
            'width': config.width,
            'height': config.height,
        }
        full_name = name.format(**fmt_params_name)
        full_desc = description.format(**fmt_params_desc)

        def _uuid(identifier):
            return uuid(category, full_name, identifier)

        # UUIDs
        uuid_pkg = _uuid('pkg')
        uuid_pads = [_uuid('pad-1'), _uuid('pad-2')]

        print('Generating {}: {}'.format(full_name, uuid_pkg))

        # General info
        lines.append('(librepcb_package {}'.format(uuid_pkg))
        lines.append(' (name "{}")'.format(full_name))
        lines.append(' (description "{}\\n\\nGenerated with {}")'.format(full_desc, generator))
        lines.append(' (keywords "{},{},{}")'.format(
            config.size_metric(), config.size_imperial(), keywords,
        ))
        lines.append(' (author "{}")'.format(author))
        lines.append(' (version "0.3")')
        lines.append(' (created {})'.format(create_date or now()))
        lines.append(' (deprecated false)')
        lines.append(' (category {})'.format(pkgcat))
        lines.append(' (pad {} (name "1"))'.format(uuid_pads[0]))
        lines.append(' (pad {} (name "2"))'.format(uuid_pads[1]))

        def add_footprint_variant(key: str, name: str, density_level: str, toe_extension: float):
            uuid_footprint = _uuid('footprint-{}'.format(key))
            uuid_text_name = _uuid('text-name-{}'.format(key))
            uuid_text_value = _uuid('text-value-{}'.format(key))
            uuid_silkscreen_top = _uuid('line-silkscreen-top-{}'.format(key))
            uuid_silkscreen_bot = _uuid('line-silkscreen-bot-{}'.format(key))
            uuid_courtyard = _uuid('polygon-courtyard-{}'.format(key))
            uuid_outline_top = _uuid('polygon-outline-top-{}'.format(key))
            uuid_outline_bot = _uuid('polygon-outline-bot-{}'.format(key))
            uuid_outline_left = _uuid('polygon-outline-left-{}'.format(key))
            uuid_outline_right = _uuid('polygon-outline-right-{}'.format(key))

            # Max boundary
            max_x = 0.0
            max_y = 0.0

            # Line width adjusted for size of element
            if config.length >= 2.0:
                silk_lw = line_width
                doc_lw = line_width
            elif config.length >= 1.0:
                silk_lw = line_width_thin
                doc_lw = line_width_thin
            else:
                silk_lw = line_width_thin
                doc_lw = line_width_thinner

            lines.append(' (footprint {}'.format(uuid_footprint))
            lines.append('  (name "{}")'.format(name))
            lines.append('  (description "")')

            # Pads
            for p in [0, 1]:
                pad_uuid = uuid_pads[p - 1]
                sign = -1 if p == 1 else 1
                # Note: We are using the gap from the actual resistors (Samsung), but calculate
                # the protrusion (toe and side) based on IPC7351.
                pad_width = config.width + get_by_density(config.length, density_level, 'side')
                pad_toe = get_by_density(config.length, density_level, 'toe') + toe_extension
                pad_length = (config.length - config.gap) / 2 + pad_toe
                dx = sign * (config.gap / 2 + pad_length / 2)  # x offset (delta-x)
                lines.append('  (pad {} (side top) (shape rect)'.format(pad_uuid))
                lines.append('   (position {} 0) (rotation 0.0) (size {} {}) (drill 0.0)'.format(
                    ff(dx),
                    ff(pad_length),
                    ff(pad_width),
                ))
                max_x = max(max_x, pad_length / 2 + dx)
                lines.append('  )')

            # Documentation
            half_gap = ff(config.gap / 2)
            dx = ff(config.length / 2)
            dy = ff(config.width / 2)
            lines.append('  (polygon {} (layer {})'.format(uuid_outline_left, 'top_documentation'))
            lines.append('   (width 0.0) (fill true) (grab_area true)')
            lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(dx, dy))  # NW
            lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(half_gap, dy))  # NE
            lines.append('   (vertex (position -{} -{}) (angle 0.0))'.format(half_gap, dy))  # SE
            lines.append('   (vertex (position -{} -{}) (angle 0.0))'.format(dx, dy))  # SW
            lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(dx, dy))  # NW
            lines.append('  )')
            lines.append('  (polygon {} (layer {})'.format(uuid_outline_right, 'top_documentation'))
            lines.append('   (width 0.0) (fill true) (grab_area true)')
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(dx, dy))  # NE
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(half_gap, dy))  # NW
            lines.append('   (vertex (position {} -{}) (angle 0.0))'.format(half_gap, dy))  # SW
            lines.append('   (vertex (position {} -{}) (angle 0.0))'.format(dx, dy))  # SE
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(dx, dy))  # NE
            lines.append('  )')
            dy = ff(config.width / 2 - doc_lw / 2)
            lines.append('  (polygon {} (layer {})'.format(uuid_outline_top, 'top_documentation'))
            lines.append('   (width {}) (fill false) (grab_area true)'.format(doc_lw))
            lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(half_gap, dy))
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(half_gap, dy))
            lines.append('  )')
            lines.append('  (polygon {} (layer {})'.format(uuid_outline_bot, 'top_documentation'))
            lines.append('   (width {}) (fill false) (grab_area true)'.format(doc_lw))
            lines.append('   (vertex (position -{} -{}) (angle 0.0))'.format(half_gap, dy))
            lines.append('   (vertex (position {} -{}) (angle 0.0))'.format(half_gap, dy))
            lines.append('  )')
            max_y = max(max_y, config.width / 2)

            # Silkscreen
            if config.length > 1.0:
                dx = ff(config.gap / 2 - silk_lw / 2 - silkscreen_clearance)
                dy = ff(config.width / 2 + silk_lw / 2)
                lines.append('  (polygon {} (layer {})'.format(uuid_silkscreen_top, 'top_placement'))
                lines.append('   (width {}) (fill false) (grab_area false)'.format(silk_lw))
                lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(dx, dy))
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(dx, dy))
                lines.append('  )')
                lines.append('  (polygon {} (layer {})'.format(uuid_silkscreen_bot, 'top_placement'))
                lines.append('   (width {}) (fill false) (grab_area false)'.format(silk_lw))
                lines.append('   (vertex (position -{} -{}) (angle 0.0))'.format(dx, dy))
                lines.append('   (vertex (position {} -{}) (angle 0.0))'.format(dx, dy))
                lines.append('  )')
                max_y = max(max_y, config.width / 2 + silk_lw)

            # Courtyard
            courtyard_excess = get_by_density(config.length, density_level, 'courtyard')
            lines.extend(indent(2, generate_courtyard(
                uuid=uuid_courtyard,
                max_x=max_x,
                max_y=max_y,
                excess_x=courtyard_excess,
                excess_y=courtyard_excess,
            )))

            # Labels
            if config.width < 2.0:
                offset = label_offset_thin
            else:
                offset = label_offset
            dy = ff(config.width / 2 + offset)  # y offset (delta-y)
            text_attrs = '(height {}) (stroke_width 0.2) ' \
                         '(letter_spacing auto) (line_spacing auto)'.format(pkg_text_height)
            lines.append('  (stroke_text {} (layer top_names)'.format(uuid_text_name))
            lines.append('   {}'.format(text_attrs))
            lines.append('   (align center bottom) (position 0.0 {}) (rotation 0.0)'.format(dy))
            lines.append('   (auto_rotate true) (mirror false) (value "{{NAME}}")')
            lines.append('  )')
            lines.append('  (stroke_text {} (layer top_values)'.format(uuid_text_value))
            lines.append('   {}'.format(text_attrs))
            lines.append('   (align center top) (position 0.0 -{}) (rotation 0.0)'.format(dy))
            lines.append('   (auto_rotate true) (mirror false) (value "{{VALUE}}")')
            lines.append('  )')

            lines.append(' )')

        add_footprint_variant('density~b', 'Density Level B (median protrusion)', 'B', 0.0)
        add_footprint_variant('density~a', 'Density Level A (max protrusion)', 'A', 0.0)
        # add_footprint_variant('density~hs', 'Hand Soldering', 'A', handsoldering_toe_extension)

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
    _make('out/chip')
    _make('out/chip/pkg')
    # Chip resistors (RESC)
    generate_pkg(
        dirpath='out/chip/pkg',
        author='Danilo B.',
        name='RESC{size_metric} ({size_imperial})',
        description='Generic chip resistor {size_metric} (imperial {size_imperial}).\\n\\n'
                    'Length: {length}mm\\nWidth: {width}mm',
        configs=[
            # Configuration: Values taken from Samsung specs.
            #        imperial, len, wid,  hght, gap
            ChipConfig('01005', .4,  .2,  0.15, 0.2),   # noqa
            ChipConfig('0201',  .6,  .3,  0.26, 0.28),  # noqa
            ChipConfig('0402', 1.0,  .5,  0.35, 0.5),   # noqa
            ChipConfig('0603', 1.6,  .8,  0.55, 0.8),   # noqa
            ChipConfig('0805', 2.0, 1.25, 0.70, 1.4),   # noqa
            ChipConfig('1206', 3.2, 1.6,  0.70, 1.8),   # noqa
            ChipConfig('1210', 3.2, 2.55, 0.70, 1.8),   # noqa
            ChipConfig('1218', 3.2, 4.6,  0.70, 1.8),   # noqa
            ChipConfig('2010', 5.0, 2.5,  0.70, 3.3),   # noqa
            ChipConfig('2512', 6.4, 3.2,  0.70, 4.6),   # noqa
        ],
        pkgcat='a20f0330-06d3-4bc2-a1fa-f8577deb6770',
        keywords='r,resistor,chip,generic',
        create_date='2018-12-19T00:08:03Z',
    )
    # J-Lead resistors (RESJ)
    generate_pkg(
        dirpath='out/chip/pkg',
        author='Danilo B.',
        name='RESJ{size_metric} ({size_imperial})',
        description='Generic J-lead resistor {size_metric} (imperial {size_imperial}).\\n\\n'
                    'Length: {length}mm\\nWidth: {width}mm',
        configs=[
            #        imperial, len,   wid,  hght, gap
            ChipConfig('4527', 11.56, 6.98, 5.84, 5.2),
        ],
        pkgcat='a20f0330-06d3-4bc2-a1fa-f8577deb6770',
        keywords='r,resistor,j-lead,generic',
        create_date='2019-01-04T23:06:17Z',
    )
    save_cache(uuid_cache_file, uuid_cache)
