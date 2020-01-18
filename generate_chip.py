"""
Generate the following packages:

- Chip resistors SMT

"""
from os import makedirs, path
from uuid import uuid4

from typing import Any, Dict, Iterable, Optional, Tuple

from common import format_float as ff
from common import format_ipc_dimension as fd
from common import generate_courtyard, indent, init_cache, now, save_cache

generator = 'librepcb-parts-generator (generate_chip.py)'

line_width = 0.25
line_width_thin = 0.15
line_width_thinner = 0.05
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


def get_by_density(length: float, level: str, key: str) -> float:
    if length >= 1.6:
        table = DENSITY_LEVELS
    else:
        table = DENSITY_LEVELS_SMALL
    return table[level][key]


# Initialize UUID cache
uuid_cache_file = 'uuid_cache_chip.csv'
uuid_cache = init_cache(uuid_cache_file)


def uuid(category: str, full_name: str, identifier: str, create: bool = True) -> str:
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
        if not create:
            raise ValueError('Unknown UUID: {}'.format(key))
        uuid_cache[key] = str(uuid4())
    return uuid_cache[key]


class BodyDimensions:
    """
    Dimensions of the physical body.
    """
    def __init__(
        self,
        length: float,
        width: float,
        height: float,
        lead_length: Optional[float] = None,
        lead_width: Optional[float] = None,
    ):
        self.length = length
        self.width = width
        self.height = height
        self.lead_length = lead_length
        self.lead_width = lead_width

    @property
    def gap(self) -> Optional[float]:
        if self.lead_length:
            return (self.length - 2 * self.lead_length)
        return None


class FootprintDimensions:
    """
    Information about the footprint itself.

     L
    +--+   +--+
    |  | G |  | W
    +--+   +--+

    L = Length, W = Width, G = Gap

    """
    def __init__(self, pad_length: float, pad_width: float, pad_gap: float):
        self.pad_length = pad_length
        self.pad_width = pad_width
        self.pad_gap = pad_gap


class ChipConfig:
    """
    Chip configuration.

    Note: Specify either footprints or gap, but not both.

    """
    def __init__(
        self,
        size_imperial: str,  # String, e.g. "1206"
        body: BodyDimensions,
        *,
        footprints: Optional[Dict[str, FootprintDimensions]] = None,
        gap: Optional[float] = None,
        meta: Optional[Dict[str, str]] = None  # Metadata that can be used in description
    ):
        self._size_imperial = size_imperial
        self.body = body
        self.footprints = footprints
        self.gap = gap
        self.meta = meta
        if self.footprints and self.gap:
            raise ValueError('Only set either footprints or gap, but not both')
        if not self.footprints and not self.gap:
            raise ValueError('Set footprints or gap')
        if self.footprints:
            for density_level in self.footprints.keys():
                if density_level not in ['A', 'B', 'C']:
                    raise ValueError('Invalid density level: {}'.format(density_level))

    def size_metric(self) -> str:
        return str(int(self.body.length * 10)).rjust(2, '0') + \
            str(int(self.body.width * 10)).rjust(2, '0')

    def size_imperial(self) -> str:
        return self._size_imperial


class PolarizationConfig:
    def __init__(
        self,
        *,
        name_marked: str,
        id_marked: str,
        name_unmarked: str,
        id_unmarked: str
    ):
        self.name_marked = name_marked
        self.id_marked = id_marked
        self.name_unmarked = name_unmarked
        self.id_unmarked = id_unmarked


def generate_pkg(
    dirpath: str,
    author: str,
    name: str,
    description: str,
    polarization: Optional[PolarizationConfig],
    configs: Iterable[ChipConfig],
    pkgcat: str,
    keywords: str,
    version: str,
    create_date: Optional[str]
) -> None:
    category = 'pkg'
    for config in configs:
        lines = []

        fmt_params = {
            'size_metric': config.size_metric(),
            'size_imperial': config.size_imperial(),
        }  # type: Dict[str, Any]
        fmt_params_name = {
            **fmt_params,
            'length': fd(config.body.length),
            'width': fd(config.body.width),
            'height': fd(config.body.height),
            'lead_length': fd(config.body.lead_length) if config.body.lead_length else None,
            'lead_width': fd(config.body.lead_width) if config.body.lead_width else None,
        }
        fmt_params_desc = {
            **fmt_params,
            'length': config.body.length,
            'width': config.body.width,
            'height': config.body.height,
            'meta': config.meta,
        }
        full_name = name.format(**fmt_params_name)
        full_desc = description.format(**fmt_params_desc)
        full_keywords = keywords.format(**fmt_params_desc).lower()

        def _uuid(identifier: str) -> str:
            return uuid(category, full_name, identifier)

        # UUIDs
        uuid_pkg = _uuid('pkg')
        if polarization:
            uuid_pads = [
                _uuid('pad-{}'.format(polarization.id_marked)),
                _uuid('pad-{}'.format(polarization.id_unmarked)),
            ]
        else:
            uuid_pads = [_uuid('pad-1'), _uuid('pad-2')]

        print('Generating pkg "{}": {}'.format(full_name, uuid_pkg))

        # General info
        lines.append('(librepcb_package {}'.format(uuid_pkg))
        lines.append(' (name "{}")'.format(full_name))
        lines.append(' (description "{}\\n\\nGenerated with {}")'.format(full_desc, generator))
        lines.append(' (keywords "{}")'.format(','.join(filter(None, [
            config.size_metric(), config.size_imperial(), full_keywords,
        ]))))
        lines.append(' (author "{}")'.format(author))
        lines.append(' (version "{}")'.format(version))
        lines.append(' (created {})'.format(create_date or now()))
        lines.append(' (deprecated false)')
        lines.append(' (category {})'.format(pkgcat))
        if polarization:
            lines.append(' (pad {} (name "{}"))'.format(uuid_pads[0], polarization.name_marked))
            lines.append(' (pad {} (name "{}"))'.format(uuid_pads[1], polarization.name_unmarked))
        else:
            lines.append(' (pad {} (name "1"))'.format(uuid_pads[0]))
            lines.append(' (pad {} (name "2"))'.format(uuid_pads[1]))

        def add_footprint_variant(
            key: str,
            name: str,
            density_level: str,
            *,
            gap: Optional[float] = None,
            footprint: Optional[FootprintDimensions] = None
        ) -> None:
            """
            Generate a footprint variant.

            Note: Either the toe extension or footprint dimensions must be set.
            """
            if gap is not None and footprint is not None:
                raise ValueError('Only toe extension or footprint may be set')
            if gap is None and footprint is None:
                raise ValueError('Either toe extension or footprint must be set')
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
            uuid_outline_around = _uuid('polygon-outline-around-{}'.format(key))
            uuid_polarization_mark = _uuid('polygon-polarization-mark-{}'.format(key))

            # Max boundary
            max_x = 0.0
            max_y = 0.0

            # Line width adjusted for size of element
            if config.body.length >= 2.0:
                silk_lw = line_width
                doc_lw = line_width
            elif config.body.length >= 1.0:
                silk_lw = line_width_thin
                doc_lw = line_width_thin
            else:
                silk_lw = line_width_thin
                doc_lw = line_width_thinner

            lines.append(' (footprint {}'.format(uuid_footprint))
            lines.append('  (name "{}")'.format(name))
            lines.append('  (description "")')

            # Pads
            if footprint is not None:
                pad_width = footprint.pad_width
                pad_length = footprint.pad_length
                pad_gap = footprint.pad_gap
                pad_dx = (pad_gap / 2 + pad_length / 2)  # x offset (delta-x)
            elif gap is not None:
                pad_gap = gap
                pad_width = config.body.width + get_by_density(config.body.length, density_level, 'side')
                pad_toe = get_by_density(config.body.length, density_level, 'toe')
                pad_length = (config.body.length - gap) / 2 + pad_toe
                pad_dx = (gap / 2 + pad_length / 2)  # x offset (delta-x)
            else:
                raise ValueError('Either footprint or gap must be set')
            for p in [0, 1]:
                pad_uuid = uuid_pads[p - 1]
                sign = -1 if p == 1 else 1
                lines.append('  (pad {} (side top) (shape rect)'.format(pad_uuid))
                lines.append('   (position {} 0.0) (rotation 0.0) (size {} {}) (drill 0.0)'.format(
                    ff(sign * pad_dx),
                    ff(pad_length),
                    ff(pad_width),
                ))
                max_x = max(max_x, pad_length / 2 + sign * pad_dx)
                lines.append('  )')
            max_y = max(max_y, config.body.width / 2)
            max_y = max(max_y, pad_width / 2)

            # Documentation
            half_gap_raw = (config.body.gap or pad_gap) / 2
            half_gap = ff(half_gap_raw)
            if footprint is None:
                # We assume that leads are across the entire width of the part (e.g. MLCC)
                dx = ff(config.body.length / 2)
                dy = ff(config.body.width / 2)
                lines.append('  (polygon {} (layer {})'.format(uuid_outline_left, 'top_documentation'))
                lines.append('   (width 0.0) (fill true) (grab_area false)')
                lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(dx, dy))  # NW
                lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(half_gap, dy))  # NE
                lines.append('   (vertex (position -{} -{}) (angle 0.0))'.format(half_gap, dy))  # SE
                lines.append('   (vertex (position -{} -{}) (angle 0.0))'.format(dx, dy))  # SW
                lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(dx, dy))  # NW
                lines.append('  )')
                lines.append('  (polygon {} (layer {})'.format(uuid_outline_right, 'top_documentation'))
                lines.append('   (width 0.0) (fill true) (grab_area false)')
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(dx, dy))  # NE
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(half_gap, dy))  # NW
                lines.append('   (vertex (position {} -{}) (angle 0.0))'.format(half_gap, dy))  # SW
                lines.append('   (vertex (position {} -{}) (angle 0.0))'.format(dx, dy))  # SE
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(dx, dy))  # NE
                lines.append('  )')
                dy = ff(config.body.width / 2 - doc_lw / 2)
                lines.append('  (polygon {} (layer {})'.format(uuid_outline_top, 'top_documentation'))
                lines.append('   (width {}) (fill false) (grab_area false)'.format(doc_lw))
                lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(half_gap, dy))
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(half_gap, dy))
                lines.append('  )')
                lines.append('  (polygon {} (layer {})'.format(uuid_outline_bot, 'top_documentation'))
                lines.append('   (width {}) (fill false) (grab_area false)'.format(doc_lw))
                lines.append('   (vertex (position -{} -{}) (angle 0.0))'.format(half_gap, dy))
                lines.append('   (vertex (position {} -{}) (angle 0.0))'.format(half_gap, dy))
                lines.append('  )')
            else:
                # We have more precise information about the lead (e.g. molded
                # packages where leads are not the full width of the package).
                dx = ff(config.body.length / 2 - doc_lw / 2)
                dy = ff(config.body.width / 2 - doc_lw / 2)
                lines.append('  (polygon {} (layer {})'.format(uuid_outline_around, 'top_documentation'))
                lines.append('   (width {}) (fill false) (grab_area false)'.format(doc_lw))
                lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(dx, dy))
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(dx, dy))
                lines.append('   (vertex (position {} -{}) (angle 0.0))'.format(dx, dy))
                lines.append('   (vertex (position -{} -{}) (angle 0.0))'.format(dx, dy))
                lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(dx, dy))
                lines.append('  )')
                dx = ff(config.body.length / 2)
                dy = ff((config.body.lead_width or footprint.pad_width) / 2)
                lines.append('  (polygon {} (layer {})'.format(uuid_outline_left, 'top_documentation'))
                lines.append('   (width 0.0) (fill true) (grab_area false)')
                lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(dx, dy))
                lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(half_gap, dy))
                lines.append('   (vertex (position -{} -{}) (angle 0.0))'.format(half_gap, dy))
                lines.append('   (vertex (position -{} -{}) (angle 0.0))'.format(dx, dy))
                lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(dx, dy))
                lines.append('  )')
                lines.append('  (polygon {} (layer {})'.format(uuid_outline_right, 'top_documentation'))
                lines.append('   (width 0.0) (fill true) (grab_area false)')
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(dx, dy))
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(half_gap, dy))
                lines.append('   (vertex (position {} -{}) (angle 0.0))'.format(half_gap, dy))
                lines.append('   (vertex (position {} -{}) (angle 0.0))'.format(dx, dy))
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(dx, dy))
                lines.append('  )')
            if polarization:
                polarization_mark_width = config.body.width / 8
                dx_outer = ff(half_gap_raw - polarization_mark_width / 2)
                dx_inner = ff(half_gap_raw - polarization_mark_width * 1.5)
                dy = ff(config.body.width / 2 - doc_lw)
                lines.append('  (polygon {} (layer {})'.format(uuid_polarization_mark, 'top_documentation'))
                lines.append('   (width 0.0) (fill true) (grab_area true)')
                lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(dx_outer, dy))
                lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(dx_inner, dy))
                lines.append('   (vertex (position -{} -{}) (angle 0.0))'.format(dx_inner, dy))
                lines.append('   (vertex (position -{} -{}) (angle 0.0))'.format(dx_outer, dy))
                lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(dx_outer, dy))
                lines.append('  )')

            # Silkscreen
            if config.body.length > 1.0:
                if polarization:
                    dx_unmarked = pad_dx + pad_length / 2
                    dx_marked = dx_unmarked + silk_lw / 2 + silkscreen_clearance
                    dy = ff(max(
                        config.body.width / 2 + silk_lw / 2,  # Based on body width
                        pad_width / 2 + silk_lw / 2 + silkscreen_clearance,  # Based on pad width
                    ))
                    lines.append('  (polygon {} (layer {})'.format(uuid_silkscreen_top, 'top_placement'))
                    lines.append('   (width {}) (fill false) (grab_area false)'.format(silk_lw))
                    lines.append('   (vertex (position {} {}) (angle 0.0))'.format(ff(dx_unmarked), dy))
                    lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(ff(dx_marked), dy))
                    lines.append('   (vertex (position -{} -{}) (angle 0.0))'.format(ff(dx_marked), dy))
                    lines.append('   (vertex (position {} -{}) (angle 0.0))'.format(ff(dx_unmarked), dy))
                    lines.append('  )')
                else:
                    assert gap is not None, \
                        "Support for non-polarized packages with irregular pads not yet fully implemented"
                    dx = ff(gap / 2 - silk_lw / 2 - silkscreen_clearance)
                    dy = ff(config.body.width / 2 + silk_lw / 2)
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

            # Courtyard
            courtyard_excess = get_by_density(config.body.length, density_level, 'courtyard')
            lines.extend(indent(2, generate_courtyard(
                uuid=uuid_courtyard,
                max_x=max_x,
                max_y=max_y,
                excess_x=courtyard_excess,
                excess_y=courtyard_excess,
            )))

            # Labels
            if config.body.width < 2.0:
                offset = label_offset_thin
            else:
                offset = label_offset
            dy = ff(config.body.width / 2 + offset)  # y offset (delta-y)
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

        if config.gap:
            add_footprint_variant('density~b', 'Density Level B (median protrusion)', 'B', gap=config.gap)
            add_footprint_variant('density~a', 'Density Level A (max protrusion)', 'A', gap=config.gap)
        elif config.footprints:
            a = config.footprints.get('A')
            b = config.footprints.get('B')
            c = config.footprints.get('C')
            if b:
                add_footprint_variant('density~b', 'Density Level B (median protrusion)', 'B', footprint=b)
            if a:
                add_footprint_variant('density~a', 'Density Level A (max protrusion)', 'A', footprint=a)
            if c:
                add_footprint_variant('density~c', 'Density Level C (min protrusion)', 'C', footprint=c)
        else:
            raise ValueError('Either gap or footprints must be set')

        lines.append(')')

        pkg_dir_path = path.join(dirpath, uuid_pkg)
        if not (path.exists(pkg_dir_path) and path.isdir(pkg_dir_path)):
            makedirs(pkg_dir_path)
        with open(path.join(pkg_dir_path, '.librepcb-pkg'), 'w') as f:
            f.write('0.1\n')
        with open(path.join(pkg_dir_path, 'package.lp'), 'w') as f:
            f.write('\n'.join(lines))
            f.write('\n')


def generate_dev(
    dirpath: str,
    author: str,
    name: str,
    description: str,
    packages: Iterable[Tuple[str, str, str]],
    cmp: str,
    cat: str,
    signals: Iterable[str],
    keywords: str,
    version: str,
    create_date: Optional[str]
) -> None:
    category = 'dev'
    for (size_metric, size_imperial, pkg_name) in packages:
        lines = []

        fmt_params = {
            'size_metric': size_metric,
            'size_imperial': size_imperial,
        }  # type: Dict[str, Any]
        full_name = name.format(**fmt_params)
        full_desc = description.format(**fmt_params)

        def _uuid(identifier: str) -> str:
            return uuid(category, full_name, identifier)

        # UUIDs
        uuid_dev = _uuid('dev')
        pkg = uuid('pkg', pkg_name, 'pkg', create=False)
        pads = [uuid('pkg', pkg_name, 'pad-{}'.format(i), create=False) for i in range(1, 3)]

        print('Generating dev "{}": {}'.format(full_name, uuid_dev))

        # General info
        lines.append('(librepcb_device {}'.format(uuid_dev))
        lines.append(' (name "{}")'.format(full_name))
        lines.append(' (description "{}\\n\\nGenerated with {}")'.format(full_desc, generator))
        lines.append(' (keywords "{},{},{}")'.format(size_metric, size_imperial, keywords))
        lines.append(' (author "{}")'.format(author))
        lines.append(' (version "{}")'.format(version))
        lines.append(' (created {})'.format(create_date or now()))
        lines.append(' (deprecated false)')
        lines.append(' (category {})'.format(cat))
        lines.append(' (component {})'.format(cmp))
        lines.append(' (package {})'.format(pkg))
        for (pad, signal) in sorted(zip(pads, signals)):
            lines.append(' (pad {} (signal {}))'.format(pad, signal))
        lines.append(')')

        dev_dir_path = path.join(dirpath, uuid_dev)
        if not (path.exists(dev_dir_path) and path.isdir(dev_dir_path)):
            makedirs(dev_dir_path)
        with open(path.join(dev_dir_path, '.librepcb-dev'), 'w') as f:
            f.write('0.1\n')
        with open(path.join(dev_dir_path, 'device.lp'), 'w') as f:
            f.write('\n'.join(lines))
            f.write('\n')


if __name__ == '__main__':
    def _make(dirpath: str) -> None:
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
        polarization=None,
        configs=[
            # Configuration: Values taken from Samsung specs.
            ChipConfig('01005', BodyDimensions(.4,   .2,  0.15), gap=0.2),   # noqa
            ChipConfig('0201',  BodyDimensions(.6,   .3,  0.26), gap=0.28),  # noqa
            ChipConfig('0402',  BodyDimensions(1.0,  .5,  0.35), gap=0.5),   # noqa
            ChipConfig('0603',  BodyDimensions(1.6,  .8,  0.55), gap=0.8),   # noqa
            ChipConfig('0805',  BodyDimensions(2.0, 1.25, 0.70), gap=1.2),   # noqa
            ChipConfig('1206',  BodyDimensions(3.2, 1.6,  0.70), gap=1.8),   # noqa
            ChipConfig('1210',  BodyDimensions(3.2, 2.55, 0.70), gap=1.8),   # noqa
            ChipConfig('1218',  BodyDimensions(3.2, 4.6,  0.70), gap=1.8),   # noqa
            ChipConfig('2010',  BodyDimensions(5.0, 2.5,  0.70), gap=3.3),   # noqa
            ChipConfig('2512',  BodyDimensions(6.4, 3.2,  0.70), gap=4.6),   # noqa
        ],
        pkgcat='a20f0330-06d3-4bc2-a1fa-f8577deb6770',
        keywords='r,resistor,chip,generic',
        version='0.3.2',
        create_date='2018-12-19T00:08:03Z',
    )
    # J-Lead resistors (RESJ)
    generate_pkg(
        dirpath='out/chip/pkg',
        author='Danilo B.',
        name='RESJ{size_metric} ({size_imperial})',
        description='Generic J-lead resistor {size_metric} (imperial {size_imperial}).\\n\\n'
                    'Length: {length}mm\\nWidth: {width}mm',
        polarization=None,
        configs=[
            ChipConfig('4527', BodyDimensions(11.56, 6.98, 5.84), gap=5.2),
        ],
        pkgcat='a20f0330-06d3-4bc2-a1fa-f8577deb6770',
        keywords='r,resistor,j-lead,generic',
        version='0.3.2',
        create_date='2019-01-04T23:06:17Z',
    )
    # Molded polarized capacitors (CAPPM)
    # Based on the table "Common Molded Body Tantalum Capacitors" in the IPC7351C draft
    # and KEMET documentation: https://content.kemet.com/datasheets/KEM_T2005_T491.pdf
    # (see Table 2: Land Dimensions / Courtyard)
    generate_pkg(
        dirpath='out/chip/pkg',
        author='Danilo B.',
        name='CAPPM{length}X{width}X{height}L{lead_length}X{lead_width}',
        description='Generic polarized molded inward-L capacitor (EIA {meta[eia]}).\\n\\n'
                    'Length: {length}mm\\nWidth: {width}mm\\nMax height: {height}mm\\n\\n'
                    'EIA Size Code: {meta[eia]}\\n'
                    'KEMET Case Code: {meta[kemet]}\\nAVX Case Code: {meta[avx]}',
        polarization=PolarizationConfig(
            name_marked='+',
            id_marked='p',
            name_unmarked='-',
            id_unmarked='n',
        ),
        configs=[
            ChipConfig('', BodyDimensions(3.2, 1.6, 1.0, 0.8, 1.2), footprints={
                'A': FootprintDimensions(2.20, 1.35, 0.62),
                'B': FootprintDimensions(1.80, 1.23, 0.82),
                'C': FootprintDimensions(1.42, 1.13, 0.98),
            }, meta={'eia': '3216-10', 'kemet': 'I', 'avx': 'K'}),
            ChipConfig('', BodyDimensions(3.2, 1.6, 1.2, 0.8, 1.2), footprints={
                'A': FootprintDimensions(2.20, 1.35, 0.62),
                'B': FootprintDimensions(1.80, 1.23, 0.82),
                'C': FootprintDimensions(1.42, 1.13, 0.98),
            }, meta={'eia': '3216-12', 'kemet': 'S', 'avx': 'S'}),
            ChipConfig('', BodyDimensions(3.2, 1.6, 1.8, 0.8, 1.2), footprints={
                'A': FootprintDimensions(2.20, 1.35, 0.62),
                'B': FootprintDimensions(1.80, 1.23, 0.82),
                'C': FootprintDimensions(1.42, 1.13, 0.98),
            }, meta={'eia': '3216-18', 'kemet': 'A', 'avx': 'A'}),
            ChipConfig('', BodyDimensions(3.5, 2.8, 1.2, 0.8, 2.2), footprints={
                'A': FootprintDimensions(2.20, 2.35, 0.92),
                'B': FootprintDimensions(1.80, 2.23, 1.12),
                'C': FootprintDimensions(1.42, 2.13, 1.28),
            }, meta={'eia': '3528-12', 'kemet': 'T', 'avx': 'T'}),
            ChipConfig('', BodyDimensions(3.5, 2.8, 2.1, 0.8, 2.2), footprints={
                'A': FootprintDimensions(2.21, 2.35, 0.92),
                'B': FootprintDimensions(1.80, 2.23, 1.12),
                'C': FootprintDimensions(1.42, 2.13, 1.28),
            }, meta={'eia': '3528-21', 'kemet': 'B', 'avx': 'B'}),
            ChipConfig('', BodyDimensions(6.0, 3.2, 1.5, 1.3, 2.2), footprints={
                'A': FootprintDimensions(2.77, 2.35, 2.37),
                'B': FootprintDimensions(2.37, 2.23, 2.57),
                'C': FootprintDimensions(1.99, 2.13, 2.73),
            }, meta={'eia': '6032-15', 'kemet': 'U', 'avx': 'W'}),
            ChipConfig('', BodyDimensions(6.0, 3.2, 2.8, 1.3, 2.2), footprints={
                'A': FootprintDimensions(2.77, 2.35, 2.37),
                'B': FootprintDimensions(2.37, 2.23, 2.57),
                'C': FootprintDimensions(1.99, 2.13, 2.73),
            }, meta={'eia': '6032-28', 'kemet': 'C', 'avx': 'C'}),
            ChipConfig('', BodyDimensions(7.3, 6.0, 3.8, 1.3, 4.1), footprints={
                'A': FootprintDimensions(2.77, 4.25, 3.68),
                'B': FootprintDimensions(2.37, 4.13, 3.87),
                'C': FootprintDimensions(1.99, 4.03, 4.03),
            }, meta={'eia': '7360-38', 'kemet': 'E', 'avx': 'V'}),
            ChipConfig('', BodyDimensions(7.3, 4.3, 2.0, 1.3, 2.4), footprints={
                'A': FootprintDimensions(2.77, 2.55, 3.67),
                'B': FootprintDimensions(2.37, 2.43, 3.87),
                'C': FootprintDimensions(1.99, 2.33, 4.03),
            }, meta={'eia': '7343-20', 'kemet': 'V', 'avx': 'Y'}),
            ChipConfig('', BodyDimensions(7.3, 4.3, 3.1, 1.3, 2.4), footprints={
                'A': FootprintDimensions(2.77, 2.55, 3.67),
                'B': FootprintDimensions(2.37, 2.43, 3.87),
                'C': FootprintDimensions(1.99, 2.33, 4.03),
            }, meta={'eia': '7343-31', 'kemet': 'D', 'avx': 'D'}),
            ChipConfig('', BodyDimensions(7.3, 4.3, 4.3, 1.3, 2.4), footprints={
                'A': FootprintDimensions(2.77, 2.55, 3.67),
                'B': FootprintDimensions(2.37, 2.43, 3.87),
                'C': FootprintDimensions(1.99, 2.33, 4.03),
            }, meta={'eia': '7343-43', 'kemet': 'X', 'avx': 'E'}),
        ],
        pkgcat='414f873f-4099-47fd-8526-bdd8419de581',
        keywords='c,capacitor,j-lead,inward-l,molded,generic,kemet {meta[kemet]},avx {meta[avx]}',
        version='0.1',
        create_date='2019-11-18T21:56:00Z',
    )
    # Generic devices
    _make('out/chip/dev')
    generate_dev(
        dirpath='out/chip/dev',
        author='Danilo B.',
        name='Resistor {size_metric} ({size_imperial})',
        description='Generic SMD resistor {size_metric} (imperial {size_imperial}).',
        packages=[
            # Metric, Imperial, Name
            ('0402', '01005', 'RESC0402 (01005)'),
            ('0603', '0201', 'RESC0603 (0201)'),
            ('1005', '0402', 'RESC1005 (0402)'),
            ('1608', '0603', 'RESC1608 (0603)'),
            ('2012', '0805', 'RESC2012 (0805)'),
            ('3216', '1206', 'RESC3216 (1206)'),
            ('3225', '1210', 'RESC3225 (1210)'),
            ('3246', '1218', 'RESC3246 (1218)'),
            ('5025', '2010', 'RESC5025 (2010)'),
            ('6432', '2512', 'RESC6432 (2512)'),
            ('11569', '4527', 'RESJ11569 (4527)'),
        ],
        cmp='ef80cd5e-2689-47ee-8888-31d04fc99174',
        cat='1039f038-20a6-4bfe-89c1-99f34fbb45bd',
        signals=[
            '3452d36e-1ce8-4b7c-8e5b-90c2e4929ed8',
            'ad623f98-9e73-49c3-9404-f7cfa99d17cd',
        ],
        keywords='r,resistor,resistance,smd,smt',
        version='0.3',
        create_date='2019-01-29T19:47:42Z',
    )
    save_cache(uuid_cache_file, uuid_cache)
