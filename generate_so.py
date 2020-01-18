"""
Generate the following SO packages:

- SOIC (both EIAJ and JEDEC)
- TSSOP (JEDEC MO-153)
- SSOP (JEDEC MO-150 and MO-152)

"""
from os import makedirs, path
from uuid import uuid4

from typing import Dict, Iterable, List, Optional

from common import format_float as ff
from common import format_ipc_dimension as fd
from common import generate_courtyard, indent, init_cache, now, save_cache

generator = 'librepcb-parts-generator (generate_so.py)'

line_width = 0.25
pkg_text_height = 1.0
silkscreen_offset = 0.150  # 150 µm
pin_package_offset = 0.762  # Distance between pad center and the package outline


# Based on IPC 7351B (Table 3-2)
DENSITY_LEVELS = {  # For pitch 0.625 mm and up
    'A': {'toe': 0.55, 'heel': 0.45, 'side': 0.05, 'courtyard': 0.50},
    'B': {'toe': 0.35, 'heel': 0.35, 'side': 0.03, 'courtyard': 0.25},
    'C': {'toe': 0.15, 'heel': 0.25, 'side': 0.01, 'courtyard': 0.10},
}
# Based on IPC 7351B (Table 3-3)
DENSITY_LEVELS_SMALL = {  # For pitch below 0.625 mm
    'A': {'toe': 0.55, 'heel': 0.45, 'side': 0.01, 'courtyard': 0.50},
    'B': {'toe': 0.35, 'heel': 0.35, 'side': -0.02, 'courtyard': 0.25},
    'C': {'toe': 0.15, 'heel': 0.25, 'side': -0.04, 'courtyard': 0.10},
}


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


def get_by_density(pitch: float, level: str, key: str) -> float:
    if pitch >= 0.625:
        table = DENSITY_LEVELS
    else:
        table = DENSITY_LEVELS_SMALL
    return table[level][key]


def get_y(pin_number: int, pin_count: int, spacing: float, grid_align: bool) -> float:
    """
    Return the y coordinate of the specified pin. Keep the pins grid aligned, if desired.

    The pin number is 1 index based. Pin 1 is at the top. The middle pin will
    be at or near 0.

    Coordinates are rounded to the next 0.001 mm.

    """
    if grid_align:
        mid = float((pin_count + 1) // 2)
    else:
        mid = (pin_count + 1) / 2
    y = -round(pin_number * spacing - mid * spacing, 3)
    if y == -0.0:  # Returns true for 0.0 too, but that doesn't matter
        return 0.0
    return y


class SoConfig:
    def __init__(
        self,
        pin_count: int,
        pitch: float,
        body_length: float,
        body_width: float,
        total_width: float,
        height: float,
        variation: Optional[str] = None,
    ):
        self.pin_count = pin_count
        self.pitch = pitch
        self.body_length = body_length
        self.body_width = body_width
        self.total_width = total_width
        self.height = height
        self.variation = variation


def generate_pkg(
    dirpath: str,
    author: str,
    name: str,
    description: str,
    configs: Iterable[SoConfig],
    lead_width_lookup: Dict[float, float],
    lead_contact_length: float,
    pkgcat: str,
    keywords: str,
    version: str,
    create_date: Optional[str],
) -> None:
    category = 'pkg'
    for config in configs:
        pitch = config.pitch
        pin_count = config.pin_count
        height = config.height
        body_width = config.body_width
        total_width = config.total_width
        body_length = config.body_length
        lead_width = lead_width_lookup[pitch]
        lead_length = (total_width - body_width) / 2

        lines = []

        full_name = name.format(
            height=fd(height),
            pitch=fd(pitch),
            pin_count=pin_count,
            body_length=fd(body_length),
            lead_span=fd(total_width),
            lead_width=fd(lead_width),
            lead_length=fd(lead_length),
        )
        full_description = description.format(
            height=height,
            pin_count=pin_count,
            pitch=pitch,
            body_length=body_length,
            body_width=body_width,
            lead_span=total_width,
            lead_width=lead_width,
            lead_length=lead_length,
            variation=config.variation,
        )

        def _uuid(identifier: str) -> str:
            return uuid(category, full_name, identifier)

        uuid_pkg = _uuid('pkg')
        uuid_pads = [_uuid('pad-{}'.format(p)) for p in range(1, pin_count + 1)]
        uuid_leads1 = [_uuid('lead-contact-{}'.format(p)) for p in range(1, pin_count + 1)]
        uuid_leads2 = [_uuid('lead-proj-{}'.format(p)) for p in range(1, pin_count + 1)]

        print('Generating {}: {}'.format(full_name, uuid_pkg))

        # General info
        lines.append('(librepcb_package {}'.format(uuid_pkg))
        lines.append(' (name "{}")'.format(full_name))
        lines.append(' (description "{}\\n\\nGenerated with {}")'.format(full_description, generator))
        lines.append(' (keywords "soic{},so{},{}")'.format(pin_count, pin_count, keywords))
        lines.append(' (author "{}")'.format(author))
        lines.append(' (version "{}")'.format(version))
        lines.append(' (created {})'.format(create_date or now()))
        lines.append(' (deprecated false)')
        lines.append(' (category {})'.format(pkgcat))
        for p in range(1, pin_count + 1):
            lines.append(' (pad {} (name "{}"))'.format(uuid_pads[p - 1], p))

        def add_footprint_variant(
            key: str,
            name: str,
            density_level: str,
        ) -> None:
            uuid_footprint = _uuid('footprint-{}'.format(key))
            uuid_silkscreen_top = _uuid('polygon-silkscreen-{}'.format(key))
            uuid_silkscreen_bot = _uuid('polygon-silkscreen2-{}'.format(key))
            uuid_outline = _uuid('polygon-outline-{}'.format(key))
            uuid_courtyard = _uuid('polygon-courtyard-{}'.format(key))
            uuid_text_name = _uuid('text-name-{}'.format(key))
            uuid_text_value = _uuid('text-value-{}'.format(key))

            # Max boundaries (pads or body)
            max_x = 0.0
            max_y = 0.0

            # Max boundaries (copper only)
            max_y_copper = 0.0

            lines.append(' (footprint {}'.format(uuid_footprint))
            lines.append('  (name "{}")'.format(name))
            lines.append('  (description "")')

            # Pad excess according to IPC density levels
            pad_heel = get_by_density(pitch, density_level, 'heel')
            pad_toe = get_by_density(pitch, density_level, 'toe')
            pad_side = get_by_density(pitch, density_level, 'side')

            # Pads
            pad_width = lead_width + pad_side
            pad_length = lead_contact_length + pad_heel + pad_toe
            pad_x_offset = total_width / 2 - lead_contact_length / 2 - pad_heel / 2 + pad_toe / 2
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
                    pxo, ff(y), ff(pad_length), ff(pad_width),
                ))
                lines.append('  )')
                max_y_copper = max(max_y_copper, y + pad_width / 2)
            max_x = max(max_x, total_width / 2 + pad_toe)

            # Documentation: Leads
            lead_contact_x_offset = total_width / 2 - lead_contact_length  # this is the inner side of the contact area
            for p in range(1, pin_count + 1):
                mid = pin_count // 2
                if p <= mid:  # left side
                    y = get_y(p, pin_count // 2, pitch, False)
                    lcxo_max = ff(-lead_contact_x_offset - lead_contact_length)
                    lcxo_min = ff(-lead_contact_x_offset)
                    body_side = ff(-body_width / 2)
                else:  # right side
                    y = -get_y(p - mid, pin_count // 2, pitch, False)
                    lcxo_min = ff(lead_contact_x_offset)
                    lcxo_max = ff(lead_contact_x_offset + lead_contact_length)
                    body_side = ff(body_width / 2)
                y_max = ff(y - lead_width / 2)
                y_min = ff(y + lead_width / 2)
                lead_uuid_ctct = uuid_leads1[p - 1]  # Contact area
                lead_uuid_proj = uuid_leads2[p - 1]  # Vertical projection
                # Contact area
                lines.append('  (polygon {} (layer top_documentation)'.format(lead_uuid_ctct))
                lines.append('   (width 0.0) (fill true) (grab_area false)')
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(lcxo_min, y_max))
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(lcxo_max, y_max))
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(lcxo_max, y_min))
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(lcxo_min, y_min))
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(lcxo_min, y_max))
                lines.append('  )')
                # Vertical projection, between contact area and body
                lines.append('  (polygon {} (layer top_documentation)'.format(lead_uuid_proj))
                lines.append('   (width 0.0) (fill true) (grab_area false)')
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(body_side, y_max))
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(lcxo_min, y_max))
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(lcxo_min, y_min))
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(body_side, y_min))
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(body_side, y_max))
                lines.append('  )')

            # Silkscreen (fully outside body)
            # Ensure minimum clearance between copper and silkscreen
            y_offset = max(silkscreen_offset - (body_length / 2 - max_y_copper), 0)
            y_max = ff(body_length / 2 + line_width / 2 + y_offset)
            y_min = ff(-body_length / 2 - line_width / 2 - y_offset)
            short_x_offset = body_width / 2 - line_width / 2
            long_x_offset = total_width / 2 - line_width / 2 + pad_toe  # Pin1 marking
            lines.append('  (polygon {} (layer top_placement)'.format(uuid_silkscreen_top))
            lines.append('   (width {}) (fill false) (grab_area false)'.format(line_width))
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(ff(-long_x_offset), y_max))  # noqa
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(ff(short_x_offset), y_max))  # noqa
            lines.append('  )')
            lines.append('  (polygon {} (layer top_placement)'.format(uuid_silkscreen_bot))
            lines.append('   (width {}) (fill false) (grab_area false)'.format(line_width))
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(ff(-short_x_offset), y_min))  # noqa
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(ff(short_x_offset), y_min))  # noqa
            lines.append('  )')

            # Documentation outline (fully inside body)
            outline_x_offset = body_width / 2 - line_width / 2
            lines.append('  (polygon {} (layer top_documentation)'.format(uuid_outline))
            lines.append('   (width {}) (fill false) (grab_area true)'.format(line_width))
            y_max = ff(body_length / 2 - line_width / 2)
            y_min = ff(-body_length / 2 + line_width / 2)
            oxo = ff(outline_x_offset)  # Used for shorter code lines below :)
            lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(oxo, y_max))
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(oxo, y_max))
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(oxo, y_min))
            lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(oxo, y_min))
            lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(oxo, y_max))
            lines.append('  )')
            max_y = max(max_y, body_length / 2)  # Body contour

            # Courtyard
            courtyard_excess = get_by_density(pitch, density_level, 'courtyard')
            lines.extend(indent(2, generate_courtyard(
                uuid=uuid_courtyard,
                max_x=max_x,
                max_y=max_y,
                excess_x=courtyard_excess,
                excess_y=courtyard_excess,
            )))

            # Labels
            y_max = ff(body_length / 2 + 1.27)
            y_min = ff(-body_length / 2 - 1.27)
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

    # SOIC

    _make('out/soic/pkg')
    configs = []  # type: List[SoConfig]
    for pin_count in [6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 28, 30, 32]:
        for height in [1.2, 1.4, 1.7, 2.7]:
            pitch = 1.27
            body_length = (pin_count / 2 - 1) * pitch + 2.0
            body_width = 5.22
            total_width = 8.42  # effective, not nominal (7.62)
            configs.append(SoConfig(pin_count, pitch, body_length, body_width, total_width, height))
    generate_pkg(
        dirpath='out/soic/pkg',
        author='Danilo B.',
        name='SOIC{pitch}P762X{height}-{pin_count}',
        description='{pin_count}-pin Small Outline Integrated Circuit (SOIC), '
                    'standardized by EIAJ.\\n\\n'
                    'Pitch: {pitch:.2f} mm\\nNominal width: 7.62mm\\nHeight: {height:.2f}mm',
        configs=configs,
        lead_width_lookup={1.27: 0.4},
        lead_contact_length=0.8,
        pkgcat='a074fabf-4912-4c29-bc6b-451bf43c2193',
        keywords='so,soic,small outline,smd,eiaj',
        version='0.2.1',
        create_date='2018-11-10T20:32:03Z',
    )
    configs = []
    for pin_count in [20, 22, 24, 28, 30, 32, 36, 40, 42, 44]:
        for height in [1.2, 1.4, 1.7, 2.7]:
            pitch = 1.27
            body_length = (pin_count / 2 - 1) * pitch + 2.0
            body_width = 12.84
            total_width = 16.04  # effective, not nominal (15.42)
            configs.append(SoConfig(pin_count, pitch, body_length, body_width, total_width, height))
    generate_pkg(
        dirpath='out/soic/pkg',
        author='Danilo B.',
        name='SOIC{pitch}P1524X{height}-{pin_count}',
        description='{pin_count}-pin Small Outline Integrated Circuit (SOIC), '
                    'standardized by EIAJ.\\n\\n'
                    'Pitch: {pitch:.2f} mm\\nNominal width: 15.24mm\\nHeight: {height:.2f}mm',
        configs=configs,
        lead_width_lookup={1.27: 0.4},
        lead_contact_length=0.8,
        pkgcat='a074fabf-4912-4c29-bc6b-451bf43c2193',
        keywords='so,soic,small outline,smd,eiaj',
        version='0.2.1',
        create_date='2018-11-10T20:32:03Z',
    )
    configs = []
    for pin_count in [6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 28, 30, 32, 36, 40, 42, 44, 48]:
        pitch = 1.27
        height = 1.75
        body_length = (pin_count / 2 - 1) * pitch + 1.6
        body_width = 3.9
        total_width = 6.0
        configs.append(SoConfig(pin_count, pitch, body_length, body_width, total_width, height))
    generate_pkg(
        dirpath='out/soic/pkg',
        author='Danilo B.',
        name='SOIC{pitch}P600X{height}-{pin_count}',
        description='{pin_count}-pin Small Outline Integrated Circuit (SOIC), '
                    'standardized by JEDEC (MS-012G).\\n\\n'
                    'Pitch: {pitch:.2f} mm\\nNominal width: 6.00mm\\nHeight: {height:.2f}mm',
        configs=configs,
        lead_width_lookup={1.27: 0.45},
        lead_contact_length=0.835,
        pkgcat='a074fabf-4912-4c29-bc6b-451bf43c2193',
        keywords='so,soic,small outline,smd,jedec',
        version='0.2.1',
        create_date='2018-11-10T20:32:03Z',
    )

    # TSSOP

    _make('out/tssop/pkg')
    generate_pkg(
        dirpath='out/tssop/pkg',
        author='Danilo B.',
        # Name according to IPC7351C
        name='TSSOP{pin_count}P{pitch}_{body_length}X{lead_span}X{height}L{lead_length}X{lead_width}',
        description='{pin_count}-pin Thin-Shrink Small Outline Package (TSSOP), '
                    'standardized by JEDEC (MO-153), variation {variation}.\\n\\n'
                    'Pitch: {pitch:.2f} mm\\nBody length: {body_length:.2f} mm\\n'
                    'Body width: {body_width:.2f} mm\\nLead span: {lead_span:.2f} mm\\n'
                    'Height: {height:.2f} mm\\n'
                    'Lead length: {lead_length:.2f} mm\\nLead width: {lead_width:.2f} mm',
        configs=[
            # pin count, pitch, body length, body width, total width, height

            # Symbols based on JEDEC MO-153:
            #        N    e     D     E1   E    A

            # 4.40mm body width
            #   0.65mm pitch
            SoConfig( 8,  0.65,  3.0, 4.4, 6.4, 1.2, 'AA'),
            SoConfig(14,  0.65,  5.0, 4.4, 6.4, 1.2, 'AB-1'),
            SoConfig(16,  0.65,  5.0, 4.4, 6.4, 1.2, 'AB'),
            SoConfig(20,  0.65,  6.5, 4.4, 6.4, 1.2, 'AC'),
            SoConfig(24,  0.65,  7.8, 4.4, 6.4, 1.2, 'AD'),
            SoConfig(28,  0.65,  9.7, 4.4, 6.4, 1.2, 'AE'),
            #   0.5mm pitch
            SoConfig(20,  0.50,  5.0, 4.4, 6.4, 1.2, 'BA'),
            SoConfig(24,  0.50,  6.5, 4.4, 6.4, 1.2, 'BB'),
            SoConfig(28,  0.50,  7.8, 4.4, 6.4, 1.2, 'BC'),
            SoConfig(30,  0.50,  7.8, 4.4, 6.4, 1.2, 'BC-1'),
            SoConfig(36,  0.50,  9.7, 4.4, 6.4, 1.2, 'BD'),
            SoConfig(38,  0.50,  9.7, 4.4, 6.4, 1.2, 'BD-1'),
            SoConfig(44,  0.50, 11.0, 4.4, 6.4, 1.2, 'BE'),
            SoConfig(50,  0.50, 12.5, 4.4, 6.4, 1.2, 'BF'),
            #   0.4mm pitch
            SoConfig(24,  0.40,  5.0, 4.4, 6.4, 1.2, 'CA'),
            SoConfig(32,  0.40,  6.5, 4.4, 6.4, 1.2, 'CB'),
            SoConfig(36,  0.40,  7.8, 4.4, 6.4, 1.2, 'CC'),
            SoConfig(48,  0.40,  9.7, 4.4, 6.4, 1.2, 'CD'),

            # 6.10mm body width
            #   0.65mm pitch
            SoConfig(24,  0.65,  7.8, 6.1, 8.1, 1.2, 'DA'),
            SoConfig(28,  0.65,  9.7, 6.1, 8.1, 1.2, 'DB'),
            SoConfig(30,  0.65,  9.7, 6.1, 8.1, 1.2, 'DB-1'),
            SoConfig(32,  0.65, 11.0, 6.1, 8.1, 1.2, 'DC'),
            SoConfig(36,  0.65, 12.5, 6.1, 8.1, 1.2, 'DD'),
            SoConfig(38,  0.65, 12.5, 6.1, 8.1, 1.2, 'DD-1'),
            SoConfig(40,  0.65, 14.0, 6.1, 8.1, 1.2, 'DE'),
            #  0.5mm pitch
            SoConfig(28,  0.50,  7.8, 6.1, 8.1, 1.2, 'EA'),
            SoConfig(36,  0.50,  9.7, 6.1, 8.1, 1.2, 'EB'),
            SoConfig(40,  0.50, 11.0, 6.1, 8.1, 1.2, 'EC'),
            SoConfig(44,  0.50, 11.0, 6.1, 8.1, 1.2, 'EC-1'),
            SoConfig(48,  0.50, 12.5, 6.1, 8.1, 1.2, 'ED'),
            SoConfig(56,  0.50, 14.0, 6.1, 8.1, 1.2, 'EE'),
            SoConfig(64,  0.50, 17.0, 6.1, 8.1, 1.2, 'EF'),
            #  0.4mm pitch
            SoConfig(36,  0.40,  7.8, 6.1, 8.1, 1.2, 'FA'),
            SoConfig(48,  0.40,  9.7, 6.1, 8.1, 1.2, 'FB'),
            SoConfig(52,  0.40, 11.0, 6.1, 8.1, 1.2, 'FC'),
            SoConfig(56,  0.40, 12.5, 6.1, 8.1, 1.2, 'FD'),
            SoConfig(64,  0.40, 14.0, 6.1, 8.1, 1.2, 'FE'),
            SoConfig(80,  0.40, 17.0, 6.1, 8.1, 1.2, 'FF'),

            # 8.00mm body width
            #   0.65mm pitch
            SoConfig(28,  0.65,  9.7, 8.0, 10.0, 1.2, 'GA'),
            SoConfig(32,  0.65, 11.0, 8.0, 10.0, 1.2, 'GB'),
            SoConfig(36,  0.65, 12.5, 8.0, 10.0, 1.2, 'GC'),
            SoConfig(40,  0.65, 14.0, 8.0, 10.0, 1.2, 'GD'),
            #   0.5mm pitch
            SoConfig(36,  0.50,  9.7, 8.0, 10.0, 1.2, 'HA'),
            SoConfig(40,  0.50, 11.0, 8.0, 10.0, 1.2, 'HB'),
            SoConfig(48,  0.50, 12.5, 8.0, 10.0, 1.2, 'HC'),
            SoConfig(56,  0.50, 14.0, 8.0, 10.0, 1.2, 'HD'),
            #   0.4mm pitch
            SoConfig(48,  0.40,  9.7, 8.0, 10.0, 1.2, 'JA'),
            SoConfig(52,  0.40, 11.0, 8.0, 10.0, 1.2, 'JB'),
            SoConfig(56,  0.40, 12.5, 8.0, 10.0, 1.2, 'JC'),
            SoConfig(60,  0.40, 12.5, 8.0, 10.0, 1.2, 'JC-1'),
            SoConfig(64,  0.40, 14.0, 8.0, 10.0, 1.2, 'JD'),
            SoConfig(68,  0.40, 14.0, 8.0, 10.0, 1.2, 'JD-1'),
        ],
        lead_width_lookup={
            0.65: 0.3,
            0.5: 0.27,
            0.4: 0.23,
        },
        lead_contact_length=0.6,
        pkgcat='241d9d5d-8f74-4740-8901-3cf51cf50091',
        keywords='so,sop,tssop,small outline package,smd',
        version='0.1',
        create_date='2019-07-21T12:15:54Z',
    )

    # SSOP

    _make('out/ssop/pkg')
    generate_pkg(
        dirpath='out/ssop/pkg',
        author='Danilo B.',
        # Name according to IPC7351C
        name='SSOP{pin_count}P{pitch}_{body_length}X{lead_span}X{height}L{lead_length}X{lead_width}',
        description='{pin_count}-pin Plastic Shrink Small Outline Package (SSOP), '
                    'standardized by JEDEC (MO-152), variation {variation}.\\n\\n'
                    'Pitch: {pitch:.2f} mm\\nBody length: {body_length:.2f} mm\\n'
                    'Body width: {body_width:.2f} mm\\nLead span: {lead_span:.2f} mm\\n'
                    'Height: {height:.2f} mm\\n'
                    'Lead length: {lead_length:.2f} mm\\nLead width: {lead_width:.2f} mm',
        configs=[
            # pin count, pitch, body length, body width, total width, height

            # Symbols based on JEDEC MO-152:
            #        N    e     D    E1   E    A

            # 4.40mm body width
            #   0.65mm pitch
            SoConfig( 8,  0.65, 3.0, 4.4, 6.4, 2.0, 'AA'),
            SoConfig(14,  0.65, 5.0, 4.4, 6.4, 2.0, 'AB-1'),
            SoConfig(16,  0.65, 5.0, 4.4, 6.4, 2.0, 'AB'),
            SoConfig(20,  0.65, 6.5, 4.4, 6.4, 2.0, 'AC'),
            SoConfig(24,  0.65, 7.8, 4.4, 6.4, 2.0, 'AD'),
            SoConfig(28,  0.65, 9.7, 4.4, 6.4, 2.0, 'AE'),
            #   0.5mm pitch
            SoConfig(20,  0.50, 5.0, 4.4, 6.4, 2.0, 'BA'),
            SoConfig(24,  0.50, 6.5, 4.4, 6.4, 2.0, 'BB'),
            SoConfig(28,  0.50, 7.8, 4.4, 6.4, 2.0, 'BC'),
            SoConfig(36,  0.50, 9.7, 4.4, 6.4, 2.0, 'BD'),
            #   0.4mm pitch
            SoConfig(24,  0.40, 5.0, 4.4, 6.4, 2.0, 'CA'),
            SoConfig(32,  0.40, 6.5, 4.4, 6.4, 2.0, 'CB'),
            SoConfig(36,  0.40, 7.8, 4.4, 6.4, 2.0, 'CC'),
            SoConfig(48,  0.40, 9.7, 4.4, 6.4, 2.0, 'CD'),

            # 6.10mm body width
            #   0.65mm pitch
            SoConfig(24,  0.65,  7.8, 6.1, 8.1, 2.0, 'DA'),
            SoConfig(28,  0.65,  9.7, 6.1, 8.1, 2.0, 'DB'),
            SoConfig(30,  0.65,  9.7, 6.1, 8.1, 2.0, 'DB-1'),
            SoConfig(32,  0.65, 11.0, 6.1, 8.1, 2.0, 'DC'),
            SoConfig(36,  0.65, 12.5, 6.1, 8.1, 2.0, 'DD'),
            SoConfig(40,  0.65, 14.0, 6.1, 8.1, 2.0, 'DE'),
            #  0.5mm pitch
            SoConfig(28,  0.50,  7.8, 6.1, 8.1, 2.0, 'EA'),
            SoConfig(36,  0.50,  9.7, 6.1, 8.1, 2.0, 'EB'),
            SoConfig(40,  0.50, 11.0, 6.1, 8.1, 2.0, 'EC'),
            SoConfig(44,  0.50, 11.0, 6.1, 8.1, 2.0, 'EC-1'),
            SoConfig(48,  0.50, 12.5, 6.1, 8.1, 2.0, 'ED'),
            SoConfig(56,  0.50, 14.0, 6.1, 8.1, 2.0, 'EE'),
            SoConfig(64,  0.50, 17.0, 6.1, 8.1, 2.0, 'EF'),
            #  0.4mm pitch
            SoConfig(36,  0.40,  7.8, 6.1, 8.1, 2.0, 'FA'),
            SoConfig(48,  0.40,  9.7, 6.1, 8.1, 2.0, 'FB'),
            SoConfig(52,  0.40, 11.0, 6.1, 8.1, 2.0, 'FC'),
            SoConfig(56,  0.40, 12.5, 6.1, 8.1, 2.0, 'FD'),
            SoConfig(64,  0.40, 14.0, 6.1, 8.1, 2.0, 'FE'),
            SoConfig(80,  0.40, 17.0, 6.1, 8.1, 2.0, 'FF'),

            # 8.00mm body width
            #   0.65mm pitch
            SoConfig(28,  0.65,  9.7, 8.0, 10.0, 2.0, 'GA'),
            SoConfig(32,  0.65, 11.0, 8.0, 10.0, 2.0, 'GB'),
            SoConfig(36,  0.65, 12.5, 8.0, 10.0, 2.0, 'GC'),
            SoConfig(40,  0.65, 14.0, 8.0, 10.0, 2.0, 'GD'),
            #   0.5mm pitch
            SoConfig(36,  0.50,  9.7, 8.0, 10.0, 2.0, 'HA'),
            SoConfig(40,  0.50, 11.0, 8.0, 10.0, 2.0, 'HB'),
            SoConfig(48,  0.50, 12.5, 8.0, 10.0, 2.0, 'HC'),
            SoConfig(56,  0.50, 14.0, 8.0, 10.0, 2.0, 'HD'),
            #   0.4mm pitch
            SoConfig(48,  0.40,  9.7, 8.0, 10.0, 2.0, 'JA'),
            SoConfig(52,  0.40, 11.0, 8.0, 10.0, 2.0, 'JB'),
            SoConfig(56,  0.40, 12.5, 8.0, 10.0, 2.0, 'JC'),
            SoConfig(60,  0.40, 12.5, 8.0, 10.0, 2.0, 'JC-1'),
            SoConfig(64,  0.40, 14.0, 8.0, 10.0, 2.0, 'JD'),
            SoConfig(68,  0.40, 14.0, 8.0, 10.0, 2.0, 'JD-1'),
        ],
        lead_width_lookup={
            0.65: 0.30,
            0.50: 0.27,
            0.40: 0.23,
        },
        lead_contact_length=0.6,
        pkgcat='3627bf02-2e6e-4d68-9ada-743fa69a4f8c',
        keywords='so,sop,ssop,small outline package,smd,jedec,mo-152',
        version='0.1',
        create_date='2019-07-21T12:55:20Z',
    )
    generate_pkg(
        dirpath='out/ssop/pkg',
        author='Danilo B.',
        # Name according to IPC7351C
        name='SSOP{pin_count}P{pitch}_{body_length}X{lead_span}X{height}L{lead_length}X{lead_width}',
        description='{pin_count}-pin Plastic Shrink Small Outline Package (SSOP), '
                    'standardized by JEDEC (MO-150), variation {variation}.\\n\\n'
                    'Pitch: {pitch:.2f} mm\\nBody length: {body_length:.2f} mm\\n'
                    'Body width: {body_width:.2f} mm\\nLead span: {lead_span:.2f} mm\\n'
                    'Height: {height:.2f} mm\\n'
                    'Lead length: {lead_length:.2f} mm\\nLead width: {lead_width:.2f} mm',
        configs=[
            # pin count, pitch, body length, body width, total width, height

            # Symbols based on JEDEC MO-150:
            #        N   e      D    E1   E    A

            SoConfig( 8, 0.65,  3.0, 5.3, 7.8, 2.0, 'AA'),
            SoConfig(14, 0.65,  6.2, 5.3, 7.8, 2.0, 'AB'),
            SoConfig(16, 0.65,  6.2, 5.3, 7.8, 2.0, 'AC'),
            SoConfig(18, 0.65,  7.2, 5.3, 7.8, 2.0, 'AD'),
            SoConfig(20, 0.65,  7.2, 5.3, 7.8, 2.0, 'AE'),
            SoConfig(22, 0.65,  8.2, 5.3, 7.8, 2.0, 'AF'),
            SoConfig(24, 0.65,  8.2, 5.3, 7.8, 2.0, 'AG'),
            SoConfig(28, 0.65, 10.2, 5.3, 7.8, 2.0, 'AH'),
            SoConfig(30, 0.65, 10.2, 5.3, 7.8, 2.0, 'AJ'),
            SoConfig(38, 0.65, 12.6, 5.3, 7.8, 2.0, 'AK'),
        ],
        lead_width_lookup={
            0.65: 0.38,
        },
        lead_contact_length=0.75,
        pkgcat='3627bf02-2e6e-4d68-9ada-743fa69a4f8c',
        keywords='so,sop,ssop,small outline package,smd,jedec,mo-150',
        version='0.1',
        create_date='2019-07-21T12:55:20Z',
    )
    save_cache(uuid_cache_file, uuid_cache)
