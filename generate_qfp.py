"""
Generate the following SO packages:

- LQFP / TQFP (only square)

Relevant standards:

- JEDEC MS-026 https://www.jedec.org/system/files/docs/MS-026D.pdf

"""
from collections import namedtuple
from copy import deepcopy
from itertools import chain
from os import makedirs, path
from uuid import uuid4

from typing import Iterable, List, Optional

from common import COURTYARD_LINE_WIDTH
from common import format_float as ff
from common import format_ipc_dimension as fd
from common import init_cache, now, save_cache, sign

generator = 'librepcb-parts-generator (generate_qfp.py)'

line_width = 0.25
pkg_text_height = 1.0
text_y_offset = 1.0
silkscreen_offset = 0.150  # 150 µm


# Initialize UUID cache
uuid_cache_file = 'uuid_cache_qfp.csv'
uuid_cache = init_cache(uuid_cache_file)


# Excess as a function of pitch according to IPC-7351C.
Excess = namedtuple('Excess', 'toe heel side courtyard')
DENSITY_LEVEL_A = {  # Most
    1.00: Excess(0.35, 0.45,  0.06, 0.40),
    0.80: Excess(0.30, 0.40,  0.05, 0.40),
    0.65: Excess(0.25, 0.35,  0.03, 0.40),
    0.50: Excess(0.20, 0.30,  0.00, 0.40),
    0.40: Excess(0.20, 0.30, -0.01, 0.40)
}
DENSITY_LEVEL_B = {  # Nominal
    1.00: Excess(0.30, 0.40,  0.05, 0.20),
    0.80: Excess(0.25, 0.35,  0.04, 0.20),
    0.65: Excess(0.20, 0.30,  0.02, 0.20),
    0.50: Excess(0.15, 0.25, -0.01, 0.20),
    0.40: Excess(0.15, 0.25, -0.02, 0.20)
}
DENSITY_LEVEL_C = {  # Least
    1.00: Excess(0.25, 0.35,  0.04, 0.10),
    0.80: Excess(0.20, 0.30,  0.03, 0.10),
    0.65: Excess(0.15, 0.25,  0.01, 0.10),
    0.50: Excess(0.10, 0.20, -0.02, 0.10),
    0.40: Excess(0.10, 0.20, -0.03, 0.10),
}


class QfpConfig:
    def __init__(
        self,
        name: str,  # e.g. QFP or LQFP
        body_size_x: float,
        body_size_y: float,
        height_nom: float,  # Nominal height (1.0 for TQFP and 1.4 for LQFP)
        height_max: float,  # Total height, A in the datasheet
        pitch: float,
        lead_count: int,
        lead_span_x: float,  # Total length from tip to tip, D in the datasheet
        lead_span_y: float,  # Total length from tip to tip, E in the datasheet
        lead_width: float,  # b in the datasheet, nominal
        keywords: str,
        name_prefix: Optional[str] = None,  # E.g. the manufacturer name
    ):
        assert body_size_x == body_size_y, 'rectangular support not yet implemented'

        self.name = name
        self.body_size_x = body_size_x
        self.body_size_y = body_size_y
        self.pitch = pitch
        self.lead_count = lead_count
        self.height_nom = height_nom
        self.height_max = height_max
        self.lead_span_x = lead_span_x
        self.lead_span_y = lead_span_y
        self.lead_width = lead_width
        self.keywords = keywords
        self.name_prefix = name_prefix or ''

        # Common dimensions
        self.lead_contact_length = 0.60  # L in the datasheet

        # Calculate lead length
        self.lead_length_x = (lead_span_x - body_size_x) / 2
        self.lead_length_y = (lead_span_y - body_size_y) / 2

    def get_configs(self) -> List['QfpConfig']:
        return [self]

    def ipc_name(self) -> str:
        return '{}{}{}P{}X{}X{}-{}'.format(
            self.name_prefix,
            self.name,
            fd(self.pitch),
            fd(self.lead_span_x),
            fd(self.lead_span_y),
            fd(self.height_nom),
            self.lead_count,
        )

    def description(self) -> str:
        if self.name == 'LQFP':
            full_name = 'Low Profile Quad Flat Package (LQFP)'
        elif self.name == 'TQFP':
            full_name = 'Thin Profile Quad Flat Package (TQFP)'
        elif self.name == 'QFP':
            full_name = 'Quad Flat Package (QFP)'
        else:
            raise ValueError('Invalid name: {}'.format(self.name))
        return '{}-pin {}, standardized by JEDEC in MS-026.\\n\\n' \
               'Pitch: {} mm\\nBody size: {}x{} mm\\nLead span: {}x{} mm\\n' \
               'Nominal height: {} mm\\nMax height: {} mm\\n\\nGenerated with {}'.format(
                   self.lead_count, full_name, self.pitch, self.body_size_x,
                   self.body_size_y, self.lead_span_x, self.lead_span_y,
                   self.height_nom, self.height_max, generator,
               )

    def excess_by_density(self, density: str) -> Excess:
        """
        Return the `Excess` based on the specified density level ('A', 'B' or
        'C') and the pitch.
        """
        try:
            if density == 'A':
                return DENSITY_LEVEL_A[self.pitch]
            elif density == 'B':
                return DENSITY_LEVEL_B[self.pitch]
            elif density == 'C':
                return DENSITY_LEVEL_C[self.pitch]
            else:
                raise ValueError('Invalid density level: {}'.format(density))
        except KeyError:
            raise ValueError('Unhandled pitch: {}'.format(self.pitch))

    def __str__(self) -> str:
        return self.ipc_name()

    def __repr__(self) -> str:
        return '<QfpConfig: {}>'.format(self.ipc_name())


class LTQfpConfig:
    """
    Generate the different L/T height variants for a certain base config.
    """
    def __init__(
        self,
        base_config: QfpConfig,  # The base config. Height will be overwritten.
        variation_t: Optional[str],  # E.g. 'AKA'
        variation_l: Optional[str],  # E.g. 'BKA'
    ):
        self.base_config = base_config
        self.variation_t = variation_t
        self.variation_l = variation_l

    def get_configs(self) -> List[QfpConfig]:
        configs = []
        for (variation, height_nom, height_max, prefix) in [
            (self.variation_t, 1.00, 1.20, 'T'),
            (self.variation_l, 1.40, 1.60, 'L'),
        ]:
            if variation is None:
                continue
            config = deepcopy(self.base_config)
            config.name = prefix + config.name
            config.height_nom = height_nom
            config.height_max = height_max
            config.keywords += ',{},{}'.format(config.name, variation).strip(',').lower()
            configs.append(config)
        return configs


JEDEC_CONFIGS = [  # May contain any type that has a `get_configs(self) -> List[QfpConfig]` method
    # Datasheet designators       D1    E1       A   e           D     E    b
    # Description                 body-x,y           ptch   pin  span-x,y

    LTQfpConfig(QfpConfig('QFP',  4.0,  4.0, -1, -1, 0.65,  20,  6.0,  6.0, 0.32, ''), 'AKA', 'BKA'),
    LTQfpConfig(QfpConfig('QFP',  4.0,  4.0, -1, -1, 0.50,  24,  6.0,  6.0, 0.22, ''), 'AKB', 'BKB'),
    LTQfpConfig(QfpConfig('QFP',  4.0,  4.0, -1, -1, 0.40,  32,  6.0,  6.0, 0.18, ''), 'AKC', 'BKC'),

    LTQfpConfig(QfpConfig('QFP',  5.0,  5.0, -1, -1, 0.50,  32,  7.0,  7.0, 0.22, ''), 'AAA', 'BAA'),
    LTQfpConfig(QfpConfig('QFP',  5.0,  5.0, -1, -1, 0.40,  40,  7.0,  7.0, 0.18, ''), 'AAB', 'BAB'),

    LTQfpConfig(QfpConfig('QFP',  7.0,  7.0, -1, -1, 0.80,  32,  9.0,  9.0, 0.37, ''), 'ABA', 'BBA'),
    LTQfpConfig(QfpConfig('QFP',  7.0,  7.0, -1, -1, 0.65,  40,  9.0,  9.0, 0.32, ''), 'ABB', 'BBB'),
    LTQfpConfig(QfpConfig('QFP',  7.0,  7.0, -1, -1, 0.50,  48,  9.0,  9.0, 0.22, ''), 'ABC', 'BBC'),
    LTQfpConfig(QfpConfig('QFP',  7.0,  7.0, -1, -1, 0.40,  64,  9.0,  9.0, 0.18, ''), 'ABD', 'BBD'),

    LTQfpConfig(QfpConfig('QFP', 10.0, 10.0, -1, -1, 1.00,  36, 12.0, 12.0, 0.42, ''), 'ACA', 'BCA'),
    LTQfpConfig(QfpConfig('QFP', 10.0, 10.0, -1, -1, 0.80,  44, 12.0, 12.0, 0.37, ''), 'ACB', 'BCB'),
    LTQfpConfig(QfpConfig('QFP', 10.0, 10.0, -1, -1, 0.65,  52, 12.0, 12.0, 0.32, ''), 'ACC', 'BCC'),
    LTQfpConfig(QfpConfig('QFP', 10.0, 10.0, -1, -1, 0.50,  64, 12.0, 12.0, 0.22, ''), 'ACD', 'BCD'),
    LTQfpConfig(QfpConfig('QFP', 10.0, 10.0, -1, -1, 0.40,  80, 12.0, 12.0, 0.18, ''), 'ACE', 'BCE'),

    LTQfpConfig(QfpConfig('QFP', 12.0, 12.0, -1, -1, 1.00,  44, 14.0, 14.0, 0.42, ''), 'ADA', 'BDA'),
    LTQfpConfig(QfpConfig('QFP', 12.0, 12.0, -1, -1, 0.80,  52, 14.0, 14.0, 0.37, ''), 'ADB', 'BDB'),
    LTQfpConfig(QfpConfig('QFP', 12.0, 12.0, -1, -1, 0.65,  64, 14.0, 14.0, 0.32, ''), 'ADC', 'BDC'),
    LTQfpConfig(QfpConfig('QFP', 12.0, 12.0, -1, -1, 0.50,  80, 14.0, 14.0, 0.22, ''), 'ADD', 'BDD'),
    LTQfpConfig(QfpConfig('QFP', 12.0, 12.0, -1, -1, 0.40, 100, 14.0, 14.0, 0.18, ''), 'ADE', 'BDE'),

    LTQfpConfig(QfpConfig('QFP', 14.0, 14.0, -1, -1, 1.00,  52, 16.0, 16.0, 0.42, ''), 'AEA', 'BEA'),
    LTQfpConfig(QfpConfig('QFP', 14.0, 14.0, -1, -1, 0.80,  64, 16.0, 16.0, 0.37, ''), 'AEB', 'BEB'),
    LTQfpConfig(QfpConfig('QFP', 14.0, 14.0, -1, -1, 0.65,  80, 16.0, 16.0, 0.32, ''), 'AEC', 'BEC'),
    LTQfpConfig(QfpConfig('QFP', 14.0, 14.0, -1, -1, 0.50, 100, 16.0, 16.0, 0.22, ''), 'AED', 'BED'),
    LTQfpConfig(QfpConfig('QFP', 14.0, 14.0, -1, -1, 0.40, 120, 16.0, 16.0, 0.18, ''), 'AEE', 'BEE'),

    LTQfpConfig(QfpConfig('QFP', 20.0, 20.0, -1, -1, 0.65, 112, 22.0, 22.0, 0.32, ''), 'AFA', 'BFA'),
    LTQfpConfig(QfpConfig('QFP', 20.0, 20.0, -1, -1, 0.50, 144, 22.0, 22.0, 0.22, ''), 'AFB', 'BFB'),
    LTQfpConfig(QfpConfig('QFP', 20.0, 20.0, -1, -1, 0.40, 176, 22.0, 22.0, 0.18, ''), 'AFC', 'BFC'),

    LTQfpConfig(QfpConfig('QFP', 24.0, 24.0, -1, -1, 0.50, 176, 26.0, 26.0, 0.22, ''), 'AGA', 'BGA'),
    LTQfpConfig(QfpConfig('QFP', 24.0, 24.0, -1, -1, 0.40, 216, 26.0, 26.0, 0.18, ''), 'AGB', 'BGB'),

    # LTQfpConfig(QfpConfig('QFP', 20.0, 14.0, -1, -1, 0.65, 100, 22.0, 16.0, 0.32, ''), 'AHA', 'BHA'),
    # LTQfpConfig(QfpConfig('QFP', 20.0, 14.0, -1, -1, 0.50, 128, 22.0, 16.0, 0.22, ''), 'AHB', 'BHB'),

    LTQfpConfig(QfpConfig('QFP', 28.0, 28.0, -1, -1, 0.65, 160, 30.0, 30.0, 0.32, ''),  None, 'BJA'),
    LTQfpConfig(QfpConfig('QFP', 28.0, 28.0, -1, -1, 0.50, 208, 30.0, 30.0, 0.22, ''),  None, 'BJB'),
    LTQfpConfig(QfpConfig('QFP', 28.0, 28.0, -1, -1, 0.40, 256, 30.0, 30.0, 0.18, ''),  None, 'BJC'),
]


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


class Pad:
    def __init__(self, x: float, y: float, orientation: str):
        self.x = x
        self.y = y
        self.orientation = orientation  # Either 'horizontal' or 'vertical'


def get_pad_coords(
    # The current pad number (1 index based)
    pad_number: int,
    # The total number of pads
    pad_count: int,
    # Pad spacing
    pitch: float,
    # X/Y offset of the pad center
    # TODO: Support rectangular elements
    pad_offset: float,
) -> Pad:
    """
    Return the x/y coordinate of the specified pad.

    The pad number is 1 index based. Pad 1 is at the top left.

    TODO: This can probably be generalized and moved into common.py.

    """
    assert pad_count % 4 == 0

    group_size = pad_count // 4
    mid = (group_size + 1) // 2
    p = (pad_number - 1) % group_size + 1

    # Determine side
    is_left = pad_number in range(1, group_size + 1)
    is_bottom = pad_number in range(group_size + 1, group_size * 2 + 1)
    is_right = pad_number in range(group_size * 2 + 1, group_size * 3 + 1)
    is_top = pad_number in range(group_size * 3 + 1, group_size * 4 + 1)

    # The dynamic offset (y for the right/left side, x for the top/bottom side)
    even_count = group_size % 2 == 0
    dynamic_offset = round((mid - p) * pitch + (pitch / 2 if even_count else 0), 3)

    # Determine factor depending on position
    if is_left:
        x = -pad_offset
        y = dynamic_offset
    elif is_bottom:
        x = -dynamic_offset
        y = -pad_offset
    elif is_right:
        x = pad_offset
        y = -dynamic_offset
    elif is_top:
        x = dynamic_offset
        y = pad_offset
    else:
        raise ValueError('Invalid pad number, out of range')

    # Determine orientation
    if is_left or is_right:
        orientation = 'horizontal'
    else:
        orientation = 'vertical'

    # Correct negative zero
    if y == -0.0:  # Returns true for 0.0 too, but that doesn't matter
        y = 0.0

    return Pad(x, y, orientation)


def generate_pkg(
    dirpath: str,
    author: str,
    configs: Iterable[QfpConfig],
    pkgcat: str,
    version: str,
    create_date: Optional[str],
) -> None:
    category = 'pkg'
    for config in configs:
        lines = []

        full_name = config.ipc_name()
        full_description = config.description()

        def _uuid(identifier: str) -> str:
            return uuid(category, full_name, identifier)

        uuid_pkg = _uuid('pkg')
        uuid_pads = [_uuid('pad-{}'.format(p)) for p in range(1, config.lead_count + 1)]
        uuid_leads1 = [_uuid('lead-contact-{}'.format(p)) for p in range(1, config.lead_count + 1)]
        uuid_leads2 = [_uuid('lead-proj-{}'.format(p)) for p in range(1, config.lead_count + 1)]

        print('Generating {}: {}'.format(full_name, uuid_pkg))

        # General info
        lines.append('(librepcb_package {}'.format(uuid_pkg))
        lines.append(' (name "{}")'.format(full_name))
        lines.append(' (description "{}")'.format(full_description, generator))
        lines.append(' (keywords "{}")'.format(config.keywords))
        lines.append(' (author "{}")'.format(author))
        lines.append(' (version "{}")'.format(version))
        lines.append(' (created {})'.format(create_date or now()))
        lines.append(' (deprecated false)')
        lines.append(' (category {})'.format(pkgcat))
        for p in range(1, config.lead_count + 1):
            lines.append(' (pad {} (name "{}"))'.format(uuid_pads[p - 1], p))

        def add_footprint_variant(
            key: str,
            name: str,
            density_level: str,
        ) -> None:
            # UUIDs
            uuid_footprint = _uuid('footprint-{}'.format(key))
            uuid_silkscreen = [_uuid('polygon-silkscreen-{}-{}'.format(quadrant, key)) for quadrant in [1, 2, 3, 4]]
            uuid_outline = _uuid('polygon-outline-{}'.format(key))
            uuid_courtyard = _uuid('polygon-courtyard-{}'.format(key))
            uuid_text_name = _uuid('text-name-{}'.format(key))
            uuid_text_value = _uuid('text-value-{}'.format(key))

            # Pad excess according to IPC density levels
            excess = config.excess_by_density(density_level)

            # Lead contact offsets
            lead_contact_x_offset = config.lead_span_x / 2 - config.lead_contact_length  # this is the inner side of the contact area

            # Position of the first and last pad
            pos_first = get_pad_coords(1, config.lead_count, config.pitch, lead_contact_x_offset)
            pos_last = get_pad_coords(config.lead_count, config.lead_count, config.pitch, lead_contact_x_offset)

            lines.append(' (footprint {}'.format(uuid_footprint))
            lines.append('  (name "{}")'.format(name))
            lines.append('  (description "")')

            # Pads
            pad_width = config.lead_width + excess.side * 2
            pad_length = config.lead_contact_length + excess.heel + excess.toe
            for p in range(1, config.lead_count + 1):
                pad_uuid = uuid_pads[p - 1]
                pad_center_offset_x = config.lead_span_x / 2 - pad_length / 2 + excess.toe
                pos = get_pad_coords(p, config.lead_count, config.pitch, pad_center_offset_x)
                pad_rotation = 90.0 if pos.orientation == 'horizontal' else 0.0
                lines.append('  (pad {} (side top) (shape rect)'.format(pad_uuid))
                lines.append('   (position {} {}) (rotation {}) (size {} {}) (drill 0.0)'.format(
                    ff(pos.x), ff(pos.y), ff(pad_rotation), ff(pad_width), ff(pad_length),
                ))
                lines.append('  )')

            # Documentation: Leads
            for p in range(1, config.lead_count + 1):
                pad_center_offset_x = config.lead_span_x / 2 - pad_length / 2
                pos = get_pad_coords(p, config.lead_count, config.pitch, lead_contact_x_offset)
                lead_uuid_ctct = uuid_leads1[p - 1]  # Contact area
                lead_uuid_proj = uuid_leads2[p - 1]  # Vertical projection

                # Contact area
                if pos.orientation == 'horizontal':
                    x1 = ff(pos.x)
                    x2 = ff(pos.x + sign(pos.x) * config.lead_contact_length)
                    y1 = ff(pos.y - config.lead_width / 2)
                    y2 = ff(pos.y + config.lead_width / 2)
                elif pos.orientation == 'vertical':
                    x1 = ff(pos.x - config.lead_width / 2)
                    x2 = ff(pos.x + config.lead_width / 2)
                    y1 = ff(pos.y)
                    y2 = ff(pos.y + sign(pos.y) * config.lead_contact_length)
                lines.append('  (polygon {} (layer top_documentation)'.format(lead_uuid_ctct))
                lines.append('   (width 0.0) (fill true) (grab_area false)')
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(x1, y1))
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(x2, y1))
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(x2, y2))
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(x1, y2))
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(x1, y1))
                lines.append('  )')
                # Vertical projection, between contact area and body
                if pos.orientation == 'horizontal':
                    x1 = ff(sign(pos.x) * config.body_size_x / 2)
                    x2 = ff(pos.x)
                    y1 = ff(pos.y - config.lead_width / 2)
                    y2 = ff(pos.y + config.lead_width / 2)
                elif pos.orientation == 'vertical':
                    x1 = x2 = y1 = y2 = ff(0)
                    x1 = ff(pos.x - config.lead_width / 2)
                    x2 = ff(pos.x + config.lead_width / 2)
                    y1 = ff(sign(pos.y) * config.body_size_y / 2)
                    y2 = ff(pos.y)
                lines.append('  (polygon {} (layer top_documentation)'.format(lead_uuid_proj))
                lines.append('   (width 0.0) (fill true) (grab_area false)')
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(x1, y1))
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(x2, y1))
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(x2, y2))
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(x1, y2))
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(x1, y1))
                lines.append('  )')

            # Silkscreen: 1 per quadrant
            # (Quadrant 1 is at the top right, the rest follows CCW)
            for quadrant in [1, 2, 3, 4]:
                uuid = uuid_silkscreen[quadrant - 1]

                x_min = abs(pos_last.x) + config.lead_width / 2 + excess.side + silkscreen_offset + line_width / 2
                x_max = config.body_size_x / 2 + line_width / 2
                y_min = abs(pos_first.y) + config.lead_width / 2 + excess.side + silkscreen_offset + line_width / 2
                y_max = config.body_size_y / 2 + line_width / 2
                vertices = [(x_min, y_max), (x_max, y_max), (x_max, y_min)]

                # Pin 1 marking line
                if quadrant == 2:
                    vertices.append((
                        config.lead_span_x / 2 + excess.toe - line_width / 2,
                        y_min,
                    ))

                lines.append('  (polygon {} (layer top_placement)'.format(uuid))
                lines.append('   (width {}) (fill false) (grab_area false)'.format(line_width))
                sign_x = 1 if quadrant in [1, 4] else -1
                sign_y = 1 if quadrant in [1, 2] else -1
                for (x, y) in vertices:
                    xx = ff(sign_x * x)
                    yy = ff(sign_y * y)
                    lines.append('   (vertex (position {} {}) (angle 0.0))'.format(xx, yy))
                lines.append('  )')

            # Documentation outline (fully inside body)
            outline_x_offset = config.body_size_x / 2 - line_width / 2
            outline_y_offset = config.body_size_y / 2 - line_width / 2
            lines.append('  (polygon {} (layer top_documentation)'.format(uuid_outline))
            lines.append('   (width {}) (fill false) (grab_area false)'.format(line_width))
            oxo = ff(outline_x_offset)  # Used for shorter code lines below :)
            oyo = ff(outline_y_offset)  # Used for shorter code lines below :)
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(oxo, oyo))  # NE
            lines.append('   (vertex (position {} -{}) (angle 0.0))'.format(oxo, oyo))  # SE
            lines.append('   (vertex (position -{} -{}) (angle 0.0))'.format(oxo, oyo))  # SW
            lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(oxo, oyo))  # NW
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(oxo, oyo))  # NE
            lines.append('  )')

            # Courtyard
            x_max = config.lead_span_x / 2 + excess.toe
            x_mid = config.body_size_x / 2
            x_min = abs(pos_last.x) + config.lead_width / 2 + excess.side
            y_max = config.lead_span_y / 2 + excess.toe
            y_mid = config.body_size_y / 2
            y_min = abs(pos_first.y) + config.lead_width / 2 + excess.side
            vertices = [  # Starting at top left
                # Top
                (-x_min,  y_max), ( x_min,  y_max), ( x_min,  y_mid), ( x_mid,  y_mid), ( x_mid,  y_min),
                # Right
                ( x_max,  y_min), ( x_max, -y_min), ( x_mid, -y_min), ( x_mid, -y_mid), ( x_min, -y_mid),
                # Bottom
                ( x_min, -y_max), (-x_min, -y_max), (-x_min, -y_mid), (-x_mid, -y_mid), (-x_mid, -y_min),
                # Left
                (-x_max, -y_min), (-x_max,  y_min), (-x_mid,  y_min), (-x_mid,  y_mid), (-x_min,  y_mid),
                # Back to top
                (-x_min,  y_max),
            ]
            lines.append('  (polygon {} (layer {})'.format(uuid_courtyard, 'top_courtyard'))
            lines.append('   (width {}) (fill false) (grab_area false)'.format(COURTYARD_LINE_WIDTH))
            for (x, y) in vertices:
                xx = ff(x + sign(x) * excess.courtyard)
                yy = ff(y + sign(y) * excess.courtyard)
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(xx, yy))
            lines.append('  )')

            # Labels
            y_offset = ff(config.lead_span_y / 2 + text_y_offset)
            text_attrs = '(height {}) (stroke_width 0.2) ' \
                         '(letter_spacing auto) (line_spacing auto)'.format(pkg_text_height)
            lines.append('  (stroke_text {} (layer top_names)'.format(uuid_text_name))
            lines.append('   {}'.format(text_attrs))
            lines.append('   (align center bottom) (position 0.0 {}) (rotation 0.0)'.format(y_offset))
            lines.append('   (auto_rotate true) (mirror false) (value "{{NAME}}")')
            lines.append('  )')
            lines.append('  (stroke_text {} (layer top_values)'.format(uuid_text_value))
            lines.append('   {}'.format(text_attrs))
            lines.append('   (align center top) (position 0.0 -{}) (rotation 0.0)'.format(y_offset))
            lines.append('   (auto_rotate true) (mirror false) (value "{{VALUE}}")')
            lines.append('  )')

            lines.append(' )')

        add_footprint_variant('density~b', 'Density Level B (median protrusion)', 'B')
        add_footprint_variant('density~a', 'Density Level A (max protrusion)', 'A')
        add_footprint_variant('density~c', 'Density Level C (min protrusion)', 'C')

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
    def _make(dirpath: str) -> None:
        if not (path.exists(dirpath) and path.isdir(dirpath)):
            makedirs(dirpath)
    _make('out')
    _make('out/qfp')
    _make('out/qfp/pkg')
    configs = list(chain.from_iterable(c.get_configs() for c in JEDEC_CONFIGS))
    generate_pkg(
        dirpath='out/qfp/pkg',
        author='Danilo B.',
        configs=configs,
        pkgcat='3363b8b1-6fa8-4041-962e-5f839cfd86b7',
        version='0.3.1',
        create_date='2019-02-07T21:03:03Z',
    )
    save_cache(uuid_cache_file, uuid_cache)
