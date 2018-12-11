"""
Generate DFN packages

"""
import numpy as np
from os import path, makedirs
from uuid import uuid4

from common import now, init_cache, save_cache
from common import format_ipc_dimension as fd
from common import format_float as ff

from dfn_configs import DfnConfig
from dfn_configs import JEDEC_CONFIGS
from dfn_configs import THIRD_CONFIGS


GENERATOR_NAME = 'librepcb-parts-generator (generate_dfn.py)'

SILKSCREEN_OFFSET = 0.15
SILKSCREEN_LINE_WIDTH = 0.254
LABEL_OFFSET = 1.0
TEXT_ATTRS = "(height 1.0) (stroke_width 0.2) (letter_spacing auto) (line_spacing auto)"

MIN_CLEARANCE = 0.15    # For checking only --> warns if violated


# Initialize UUID cache
uuid_cache_file = 'uuid_cache_dfn.csv'
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


def generate_pkg(
    dirpath: str,
    author: str,
    name: str,
    description: str,
    pkgcat: str,
    keywords: str,
    config: DfnConfig,
    make_exposed: bool,
):
    category = 'pkg'
    lines = []

    full_name = name.format(length=fd(config.length),
                            width=fd(config.width),
                            height=fd(config.height_nominal),
                            pin_count=config.pin_count,
                            pitch=fd(config.pitch))

    # Add pad length for otherwise identical names/packages
    if config.print_pad:
        full_name += "P{:s}".format(fd(config.lead_length))

    if make_exposed:
        # According to: http://www.ocipcdc.org/archive/What_is_New_in_IPC-7351C_03_11_2015.pdf
        exp_width = fd(config.exposed_width)
        exp_length = fd(config.exposed_length)
        if exp_width == exp_length:
            full_name += f"T{exp_width}"
        else:
            full_name += f"T{exp_width}X{exp_length}"

    full_description = description.format(height=config.height,
                                          pin_count=config.pin_count,
                                          pitch=config.pitch,
                                          width=config.width,
                                          length=config.length)
    if make_exposed:
        full_description += "\\nExposed Pad: {:.2f} x {:.2f} mm".format(
                config.exposed_width, config.exposed_length)

    def _uuid(identifier):
        return uuid(category, full_name, identifier)

    uuid_pkg = _uuid('pkg')
    uuid_pads = [_uuid('pad-{}'.format(p)) for p in range(1, config.pin_count + 1)]

    if make_exposed:
        uuid_exp = _uuid('exposed')

    print('Generating {}: {}'.format(full_name, uuid_pkg))

    # General info
    lines.append('(librepcb_package {}'.format(uuid_pkg))
    lines.append(' (name "{}")'.format(full_name))
    lines.append(' (description "{}\\n\\nGenerated with {}")'.format(full_description,
                                                                     GENERATOR_NAME))
    lines.append(' (keywords "dfn{}")'.format(config.pin_count, config.pin_count, keywords))
    lines.append(' (author "{}")'.format(author))
    lines.append(' (version "0.1")')
    lines.append(' (created {})'.format(now()))
    lines.append(' (deprecated false)')
    lines.append(' (category {})'.format(pkgcat))

    # Create Pad UUIDs
    for p in range(1, config.pin_count + 1):
        lines.append(' (pad {} (name "{}"))'.format(uuid_pads[p - 1], p))
    if make_exposed:
        lines.append(' (pad {} (name "{}"))'.format(uuid_exp, 'Exposed Pad'))

    # Create Footprint function
    def _generate_footprint(key: str, name: str, pad_extension: float):
        # Create Meta-data
        uuid_footprint = _uuid('footprint-{}'.format(key))
        lines.append(' (footprint {}'.format(uuid_footprint))
        lines.append('  (name "{}")'.format(name))
        lines.append('  (description "")')

        # Place pads
        for pad_idx, pad_nr in enumerate(range(1, config.pin_count + 1)):
            pad_width = config.lead_width
            pad_length = config.lead_length + pad_extension

            pad_pos_x = config.width / 2 - config.lead_length / 2 + pad_extension / 2

            half_n_pads = config.pin_count // 2
            pad_pos_y = get_y(pad_idx % half_n_pads + 1, half_n_pads, config.pitch, False)

            if pad_idx < (config.pin_count / 2):
                pad_pos_x = - pad_pos_x
            else:
                pad_pos_y = - pad_pos_y

            lines.append('  (pad {} (side top) (shape rect)'.format(uuid_pads[pad_idx]))
            lines.append('   (position {} {}) (rotation 0.0) (size {} {}) (drill 0.0)'.format(
                         ff(pad_pos_x), ff(pad_pos_y),
                         ff(pad_length), ff(pad_width)))
            lines.append('  )')

        # Make exposed pad, if required
        if make_exposed:
            lines.append('  (pad {} (side top) (shape rect)'.format(uuid_exp))
            lines.append('   (position 0.0 0.0) (rotation 0.0) (size {} {}) (drill 0.0)'.format(
                         ff(config.exposed_length), ff(config.exposed_width)))
            lines.append('  )')

            # Measure clearance pad-exposed pad
            clearance = abs(pad_pos_x) - (pad_length / 2) - (config.exposed_length / 2)
            if np.around(clearance, decimals=2) < MIN_CLEARANCE:
                print(f"Warning: minimal clearance violated in {full_name}: {clearance:.2f} < {MIN_CLEARANCE:.2f}")

        # Create Silk Screen (lines and dot only)
        silk_down = (config.length / 2 - SILKSCREEN_OFFSET -
                     get_y(1, half_n_pads, config.pitch, False) -
                     config.lead_width / 2 -
                     SILKSCREEN_LINE_WIDTH / 2)    # required for round ending of line

        for idx, silkscreen_pos in enumerate([-1, 1]):
            uuid_silkscreen_poly = _uuid('polygon-silkscreen-{}-{}'.format(key, idx))
            lines.append('  (polygon {} (layer top_placement)'.format(uuid_silkscreen_poly))
            lines.append('   (width {}) (fill false) (grab_area false)'.format(
                SILKSCREEN_LINE_WIDTH))
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(
                         ff(-config.width / 2),
                         ff(silkscreen_pos * (config.length / 2 - silk_down))))
            # If this is negative, the silkscreen line has to be moved away from
            # the real position, in order to keep the required distance to the
            # pad. We then only draw a single line, so we can omit the parts below.
            if silk_down > 0:
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(
                             ff(-config.width / 2),
                             ff(silkscreen_pos * config.length / 2)))
                lines.append('   (vertex (position {} {}) (angle 0.0))'.format(
                             ff(config.width / 2),
                             ff(silkscreen_pos * config.length / 2)))
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(
                         ff(config.width / 2),
                         ff(silkscreen_pos * (config.length / 2 - silk_down))))

            lines.append('  )')

        uuid_silkscreen_circ = _uuid('circle-silkscreen-{}'.format(key))
        lines.append('  (circle {} (layer top_placement)'.format(uuid_silkscreen_circ))
        lines.append('   (width 0.0) (fill true) (grab_area false) '
                     '(diameter {}) (position {} {})'.format(
                         ff(SILKSCREEN_LINE_WIDTH),
                         ff(-config.width / 2 - SILKSCREEN_LINE_WIDTH),
                         ff(config.length / 2 + SILKSCREEN_LINE_WIDTH)
                     ))
        lines.append('  )')

        # Create leads on docu
        uuid_leads = [_uuid('lead-{}'.format(p)) for p in range(1, config.pin_count + 1)]
        for pad_idx, pad_nr in enumerate(range(1, config.pin_count + 1)):
            lead_uuid = uuid_leads[pad_idx]

            # Make silkscreen lead exact pad width and length
            half_n_pads = config.pin_count // 2
            pad_pos_y = get_y(pad_idx % half_n_pads + 1, half_n_pads, config.pitch, False)
            if pad_idx >= (config.pin_count / 2):
                pad_pos_y = - pad_pos_y
            y_min = pad_pos_y - config.lead_width / 2
            y_max = pad_pos_y + config.lead_width / 2

            x_max = config.width / 2
            x_min = x_max - config.lead_length
            if pad_idx < (config.pin_count / 2):
                x_min, x_max = - x_min, - x_max

            lines.append('  (polygon {} (layer top_documentation)'.format(lead_uuid))
            lines.append('   (width 0.0) (fill true) (grab_area false)')
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(x_min, y_max))
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(x_max, y_max))
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(x_max, y_min))
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(x_min, y_min))
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(x_min, y_max))
            lines.append('  )')

            # Add name and value labels
            uuid_text_name = _uuid('text-name-{}'.format(key))
            uuid_text_value = _uuid('text-value-{}'.format(key))

            lines.append('  (stroke_text {} (layer top_names)'.format(uuid_text_name))
            lines.append('   {}'.format(TEXT_ATTRS))
            lines.append('   (align center bottom) (position 0.0 {}) (rotation 0.0)'.format(
                 config.length / 2 + LABEL_OFFSET))
            lines.append('   (auto_rotate true) (mirror false) (value "{{NAME}}")')
            lines.append('  )')
            lines.append('  (stroke_text {} (layer top_values)'.format(uuid_text_value))
            lines.append('   {}'.format(TEXT_ATTRS))
            lines.append('   (align center top) (position 0.0 {}) (rotation 0.0)'.format(
                -config.length / 2 - LABEL_OFFSET))
            lines.append('   (auto_rotate true) (mirror false) (value "{{VALUE}}")')
            lines.append('  )')

        # Closing parenthese for footprint
        lines.append(' )')

    # Apply function to available footprints
    _generate_footprint('reflow', 'reflow', 0.0)
    _generate_footprint('hand-soldering', 'hand soldering', 0.5)

    # Final closing parenthese
    lines.append(')')

    # Save package
    pkg_dir_path = path.join(dirpath, uuid_pkg)
    if not (path.exists(pkg_dir_path) and path.isdir(pkg_dir_path)):
        makedirs(pkg_dir_path)
    with open(path.join(pkg_dir_path, '.librepcb-pkg'), 'w') as f:
        f.write('0.1\n')
    with open(path.join(pkg_dir_path, 'package.lp'), 'w') as f:
        f.write('\n'.join(lines))
        f.write('\n')

    return full_name


if __name__ == '__main__':
    def _make(dirpath: str):
        if not (path.exists(dirpath) and path.isdir(dirpath)):
            makedirs(dirpath)
    _make('out')
    _make('out/dfn')
    _make('out/dfn/pkg')

    generated_packages = []

    for config in JEDEC_CONFIGS:
        # Find out which configs to create
        if config.exposed_width > 0 and config.exposed_length > 0:
            if config.no_exp:
                exposed_settings = [True, False]
            else:
                exposed_settings = [True]
        else:
            exposed_settings = [False]

        for make_exposed in exposed_settings:
            name = generate_pkg(
                dirpath='out/dfn/pkg',
                author='Hannes Badertscher',
                name='DFN{pitch}P{length}X{width}X{height}-{pin_count}',
                description='{pin_count}-pin Dual Flat No-Lead package (DFN), '
                            'standardized by JEDEC MO-229F.\\n\\n'
                            'Pitch: {pitch:.2f} mm\\n'
                            'Nominal width: {width:.2f} mm\\n'
                            'Nominal length: {length:.2f} mm\\n'
                            'Height: {height:.2f}mm',
                pkgcat='88cbb15c-2b69-4612-8764-c5d323f88f13',
                keywords='dfn',
                config=config,
                make_exposed=make_exposed,
            )
            if name not in generated_packages:
                generated_packages.append(name)
            else:
                print(f"Duplicate name found: {name}")

    _make('out/3rd_party')
    _make('out/3rd_party/pkg')

    for config in THIRD_CONFIGS:
        # Find out which configs to create
        if config.exposed_width > 0.0 and config.exposed_length > 0.0:
            if config.no_exp:
                exposed_settings = [True, False]
            else:
                exposed_settings = [True]
        else:
            exposed_settings = [False]

        for make_exposed in exposed_settings:
            name = generate_pkg(
                dirpath='out/3rd_party/pkg',
                author='Hannes Badertscher',
                name='DFN{pitch}P{length}X{width}X{height}-{pin_count}',
                description='{pin_count}-pin Dual Flat No-Lead package (DFN), '
                            'Pitch: {pitch:.2f} mm\\n'
                            'Nominal width: {width:.2f} mm\\n'
                            'Nominal length: {length:.2f} mm\\n'
                            'Height: {height:.2f}mm',
                pkgcat='88cbb15c-2b69-4612-8764-c5d323f88f13',
                keywords='dfn',
                config=config,
                make_exposed=make_exposed,
            )
            if name not in generated_packages:
                generated_packages.append(name)
            else:
                print(f"Duplicate name found: {name}")

    save_cache(uuid_cache_file, uuid_cache)
