"""
Generate DFN packages

"""

import sys
from os import path
from uuid import uuid4

from typing import List, Optional

from common import format_ipc_dimension as fd
from common import init_cache, now, save_cache
from dfn_configs import JEDEC_CONFIGS, THIRD_CONFIGS, DfnConfig
from entities.common import (
    Align,
    Angle,
    Author,
    Category,
    Circle,
    Created,
    Deprecated,
    Description,
    Diameter,
    Fill,
    GeneratedBy,
    GrabArea,
    Height,
    Keywords,
    Layer,
    Name,
    Polygon,
    Position,
    Position3D,
    Rotation,
    Rotation3D,
    Value,
    Version,
    Vertex,
    Width,
    generate_courtyard,
)
from entities.package import (
    AssemblyType,
    AutoRotate,
    ComponentSide,
    CopperClearance,
    Footprint,
    Footprint3DModel,
    FootprintPad,
    LetterSpacing,
    LineSpacing,
    Mirror,
    Package,
    Package3DModel,
    PackagePad,
    PackagePadUuid,
    PadFunction,
    Shape,
    ShapeRadius,
    Size,
    SolderPasteConfig,
    StopMaskConfig,
    StrokeText,
    StrokeWidth,
)

GENERATOR_NAME = 'librepcb-parts-generator (generate_dfn.py)'

SILKSCREEN_OFFSET = 0.15
SILKSCREEN_LINE_WIDTH = 0.254
LABEL_OFFSET = 1.0
COURTYARD_EXCESS = 0.2

MIN_CLEARANCE = 0.20  # For checking only --> warns if violated
MIN_TRACE = 0.10


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


def generate_pkg(
    author: str,
    name: str,
    description: str,
    pkgcat: str,
    keywords: str,
    config: DfnConfig,
    make_exposed: bool,
    generate_3d_models: bool,
    create_date: Optional[str] = None,
) -> str:
    category = 'pkg'

    full_name = name.format(
        length=fd(config.length),
        width=fd(config.width),
        height=fd(config.height_nominal),
        pin_count=config.pin_count,
        pitch=fd(config.pitch),
    )

    # Add pad length for otherwise identical names/packages
    if config.print_pad:
        full_name += 'P{:s}'.format(fd(config.lead_length))

    if make_exposed:
        # According to: http://www.ocipcdc.org/archive/What_is_New_in_IPC-7351C_03_11_2015.pdf
        exp_width = fd(config.exposed_width)
        exp_length = fd(config.exposed_length)
        if exp_width == exp_length:
            full_name += 'T{}'.format(exp_width)
        else:
            full_name += 'T{}X{}'.format(exp_width, exp_length)

    # Override name if specified
    if config.name:
        full_name = config.name

    full_description = description.format(
        height=config.height_nominal,
        pin_count=config.pin_count,
        pitch=config.pitch,
        width=config.width,
        length=config.length,
    )
    if make_exposed:
        full_description += '\nExposed Pad: {:.2f} x {:.2f} mm'.format(
            config.exposed_width, config.exposed_length
        )
    if config.print_pad:
        full_description += '\nPad length: {:.2f} mm'.format(config.lead_length)
    full_description += '\n\nGenerated with {}'.format(GENERATOR_NAME)

    if config.keywords:
        full_keywords = 'dfn{},{},{}'.format(config.pin_count, keywords, config.keywords.lower())
    else:
        full_keywords = 'dfn{},{}'.format(config.pin_count, keywords)

    def _uuid(identifier: str) -> str:
        return uuid(category, full_name, identifier)

    uuid_pkg = _uuid('pkg')
    uuid_pads = [_uuid('pad-{}'.format(p)) for p in range(1, config.pin_count + 1)]

    if make_exposed:
        uuid_exp = _uuid('exposed')

    print('Generating {}: {}'.format(full_name, uuid_pkg))

    # Create package
    package = Package(
        uuid=uuid_pkg,
        name=Name(full_name),
        description=Description(full_description),
        keywords=Keywords(full_keywords),
        author=Author(author),
        version=Version('0.2'),
        created=Created(create_date or now()),
        deprecated=Deprecated(False),
        generated_by=GeneratedBy(''),
        categories=[Category(pkgcat)],
        assembly_type=AssemblyType.SMT,
    )

    # Create pads
    for p in range(1, config.pin_count + 1):
        package.add_pad(PackagePad(uuid_pads[p - 1], Name(str(p))))
    if make_exposed:
        package.add_pad(PackagePad(uuid_exp, Name('ExposedPad')))

    # Create Footprint function
    def _generate_footprint(key: str, name: str, pad_extension: float) -> None:
        # Create Meta-data
        uuid_footprint = _uuid('footprint-{}'.format(key))
        footprint = Footprint(
            uuid=uuid_footprint,
            name=Name(name),
            description=Description(''),
            position_3d=Position3D.zero(),
            rotation_3d=Rotation3D.zero(),
        )
        package.add_footprint(footprint)

        pad_length = config.lead_length + config.toe_heel + pad_extension
        exposed_length = config.exposed_length
        abs_pad_pos_x = (
            (config.width / 2)
            - (config.lead_length / 2)
            + (config.toe_heel / 2)
            + (pad_extension / 2)
        )

        # Check clearance and make pads smaller if required
        if make_exposed:
            clearance = (config.width / 2) - config.lead_length - (exposed_length / 2)
            if clearance < MIN_CLEARANCE:
                print('Increasing clearance from {:.2f} to {:.2f}'.format(clearance, MIN_CLEARANCE))
                d_clearance = (MIN_CLEARANCE - clearance) / 2
                pad_length = pad_length - d_clearance
                exposed_length = exposed_length - 2 * d_clearance
                abs_pad_pos_x = abs_pad_pos_x + (d_clearance / 2)

            if exposed_length < MIN_TRACE:
                print(
                    'Increasing exposed path width from {:.2f} to {:.2f}'.format(
                        exposed_length, MIN_TRACE
                    )
                )
                d_exp = MIN_TRACE - exposed_length
                exposed_length = exposed_length + d_exp
                pad_length = pad_length - (d_exp / 2)
                abs_pad_pos_x = abs_pad_pos_x + (d_exp / 4)

        # Place pads
        for pad_idx, pad_nr in enumerate(range(1, config.pin_count + 1)):
            half_n_pads = config.pin_count // 2
            pad_pos_y = get_y(pad_idx % half_n_pads + 1, half_n_pads, config.pitch, False)

            if pad_idx < (config.pin_count / 2):
                pad_pos_x = -abs_pad_pos_x
            else:
                pad_pos_x = abs_pad_pos_x
                pad_pos_y = -pad_pos_y

            footprint.add_pad(
                FootprintPad(
                    uuid=uuid_pads[pad_idx],
                    side=ComponentSide.TOP,
                    shape=Shape.ROUNDED_RECT,
                    position=Position(pad_pos_x, pad_pos_y),
                    rotation=Rotation(0),
                    size=Size(pad_length, config.lead_width),
                    radius=ShapeRadius(0),
                    stop_mask=StopMaskConfig(StopMaskConfig.AUTO),
                    solder_paste=SolderPasteConfig.AUTO,
                    copper_clearance=CopperClearance(0.0),
                    function=PadFunction.STANDARD_PAD,
                    package_pad=PackagePadUuid(uuid_pads[pad_idx]),
                    holes=[],
                )
            )

        # Make exposed pad, if required
        # TODO: Handle pin1_corner_dx_dy in config once custom pad shapes are possible
        if make_exposed:
            footprint.add_pad(
                FootprintPad(
                    uuid=uuid_exp,
                    side=ComponentSide.TOP,
                    shape=Shape.ROUNDED_RECT,
                    position=Position(0, 0),
                    rotation=Rotation(0),
                    size=Size(exposed_length, config.exposed_width),
                    radius=ShapeRadius(0),
                    stop_mask=StopMaskConfig(StopMaskConfig.AUTO),
                    solder_paste=SolderPasteConfig.AUTO,
                    copper_clearance=CopperClearance(0.0),
                    function=PadFunction.STANDARD_PAD,
                    package_pad=PackagePadUuid(uuid_exp),
                    holes=[],
                )
            )

            # Measure clearance pad-exposed pad
            clearance = abs(pad_pos_x) - (pad_length / 2) - (exposed_length / 2)
            if round(clearance, ndigits=2) < MIN_CLEARANCE:
                print(
                    'Warning: minimal clearance violated in {}: {:.4f} < {:.2f}'.format(
                        full_name, clearance, MIN_CLEARANCE
                    )
                )

        # Create Silk Screen (lines and dot only)
        silk_down = (
            config.length / 2
            - SILKSCREEN_OFFSET
            - get_y(1, half_n_pads, config.pitch, False)
            - config.lead_width / 2
            - SILKSCREEN_LINE_WIDTH / 2
        )  # required for round ending of line

        # Measure clearance silkscreen to exposed pad
        silk_top_line_height = config.length / 2
        if make_exposed:
            silk_clearance = (
                silk_top_line_height - (SILKSCREEN_LINE_WIDTH / 2) - (config.exposed_width / 2)
            )
            if round(silk_clearance, ndigits=2) < SILKSCREEN_OFFSET:
                silk_top_line_height = silk_top_line_height + (SILKSCREEN_OFFSET - silk_clearance)
                silk_down = silk_down + (SILKSCREEN_OFFSET - silk_clearance)
                print(
                    'Increasing exp-silk clearance from {:.4f} to {:.2f}'.format(
                        silk_clearance, SILKSCREEN_OFFSET
                    )
                )

        # Silkscreen
        for idx, silkscreen_pos in enumerate([-1, 1]):
            uuid_silkscreen_poly = _uuid('polygon-silkscreen-{}-{}'.format(key, idx))
            vertices = [
                Vertex(
                    Position(
                        -config.width / 2, silkscreen_pos * (silk_top_line_height - silk_down)
                    ),
                    Angle(0),
                ),
            ]
            # If this is negative, the silkscreen line has to be moved away from
            # the real position, in order to keep the required distance to the
            # pad. We then only draw a single line, so we can omit the parts below.
            if silk_down > 0:
                vertices.append(
                    Vertex(
                        Position(-config.width / 2, silkscreen_pos * silk_top_line_height), Angle(0)
                    )
                )
                vertices.append(
                    Vertex(
                        Position(config.width / 2, silkscreen_pos * silk_top_line_height), Angle(0)
                    )
                )
            vertices.append(
                Vertex(
                    Position(config.width / 2, silkscreen_pos * (silk_top_line_height - silk_down)),
                    Angle(0),
                )
            )
            footprint.add_polygon(
                Polygon(
                    uuid=uuid_silkscreen_poly,
                    layer=Layer('top_legend'),
                    width=Width(SILKSCREEN_LINE_WIDTH),
                    fill=Fill(False),
                    grab_area=GrabArea(False),
                    vertices=vertices,
                )
            )

        # Create leads on docu
        uuid_leads = [_uuid('lead-{}'.format(p)) for p in range(1, config.pin_count + 1)]
        for pad_idx, pad_nr in enumerate(range(1, config.pin_count + 1)):
            lead_uuid = uuid_leads[pad_idx]

            # Make silkscreen lead exact pad width and length
            half_n_pads = config.pin_count // 2
            pad_pos_y = get_y(pad_idx % half_n_pads + 1, half_n_pads, config.pitch, False)
            if pad_idx >= (config.pin_count / 2):
                pad_pos_y = -pad_pos_y
            y_min = pad_pos_y - config.lead_width / 2
            y_max = pad_pos_y + config.lead_width / 2

            x_max = config.width / 2
            x_min = x_max - config.lead_length
            if pad_idx < (config.pin_count / 2):
                x_min, x_max = -x_min, -x_max

            footprint.add_polygon(
                Polygon(
                    uuid=lead_uuid,
                    layer=Layer('top_documentation'),
                    width=Width(0),
                    fill=Fill(True),
                    grab_area=GrabArea(False),
                    vertices=[
                        Vertex(Position(x_min, y_max), Angle(0)),
                        Vertex(Position(x_max, y_max), Angle(0)),
                        Vertex(Position(x_max, y_min), Angle(0)),
                        Vertex(Position(x_min, y_min), Angle(0)),
                        Vertex(Position(x_min, y_max), Angle(0)),
                    ],
                )
            )

        # Create exposed pad on docu
        if make_exposed:
            uuid_docu_exposed = _uuid('lead-exposed')
            x_min, x_max = -config.exposed_length / 2, config.exposed_length / 2
            y_min, y_max = -config.exposed_width / 2, config.exposed_width / 2
            footprint.add_polygon(
                Polygon(
                    uuid=uuid_docu_exposed,
                    layer=Layer('top_documentation'),
                    width=Width(0),
                    fill=Fill(True),
                    grab_area=GrabArea(False),
                    vertices=[
                        Vertex(Position(x_min, y_max), Angle(0)),
                        Vertex(Position(x_max, y_max), Angle(0)),
                        Vertex(Position(x_max, y_min), Angle(0)),
                        Vertex(Position(x_min, y_min), Angle(0)),
                        Vertex(Position(x_min, y_max), Angle(0)),
                    ],
                )
            )

        # Create body outline on docu
        uuid_body_outline = _uuid('body-outline')
        outline_line_width = 0.2
        dx = config.width / 2 - outline_line_width / 2
        dy = config.length / 2 - outline_line_width / 2
        footprint.add_polygon(
            Polygon(
                uuid=uuid_body_outline,
                layer=Layer('top_documentation'),
                width=Width(outline_line_width),
                fill=Fill(False),
                grab_area=GrabArea(False),
                vertices=[
                    Vertex(Position(-dx, dy), Angle(0)),
                    Vertex(Position(dx, dy), Angle(0)),
                    Vertex(Position(dx, -dy), Angle(0)),
                    Vertex(Position(-dx, -dy), Angle(0)),
                    Vertex(Position(-dx, dy), Angle(0)),
                ],
            )
        )

        if config.extended_doc_fn:

            def _get_uuid(identifier: str) -> str:
                return _uuid(identifier + '-' + key)

            config.extended_doc_fn(config, _get_uuid, footprint)

        # As discussed in https://github.com/LibrePCB-Libraries/LibrePCB_Base.lplib/pull/16
        # the silkscreen circle should have size SILKSCREEN_LINE_WIDTH for small packages,
        # and twice the size for larger packages. We define small to be either W or L <3.0mm
        # and large if both W and L >= 3.0mm
        if config.width >= 3.0 and config.length >= 3.0:
            silkscreen_circ_dia = 2.0 * SILKSCREEN_LINE_WIDTH
        else:
            silkscreen_circ_dia = SILKSCREEN_LINE_WIDTH

        if silkscreen_circ_dia == SILKSCREEN_LINE_WIDTH:
            silk_circ_y = config.length / 2 + silkscreen_circ_dia
            silk_circ_x = -config.width / 2 - SILKSCREEN_LINE_WIDTH
        else:
            silk_circ_y = config.length / 2 + SILKSCREEN_LINE_WIDTH / 2
            silk_circ_x = -config.width / 2 - silkscreen_circ_dia

        # Move silkscreen circle upwards if the line is moved too
        if silk_down < 0:
            silk_circ_y = silk_circ_y - silk_down

        uuid_silkscreen_circ = _uuid('circle-silkscreen-{}'.format(key))
        footprint.add_circle(
            Circle(
                uuid_silkscreen_circ,
                Layer('top_legend'),
                Width(0.0),
                Fill(True),
                GrabArea(False),
                Diameter(silkscreen_circ_dia),
                Position(silk_circ_x, silk_circ_y),
            )
        )

        # Package Outline
        dx = config.width / 2
        dy = config.length / 2
        footprint.add_polygon(
            Polygon(
                uuid=_uuid('polygon-outline-{}'.format(key)),
                layer=Layer('top_package_outlines'),
                width=Width(0),
                fill=Fill(False),
                grab_area=GrabArea(False),
                vertices=[
                    Vertex(Position(-dx, dy), Angle(0)),  # NW
                    Vertex(Position(dx, dy), Angle(0)),  # NE
                    Vertex(Position(dx, -dy), Angle(0)),  # SE
                    Vertex(Position(-dx, -dy), Angle(0)),  # SW
                ],
            )
        )

        # Courtyard
        footprint.add_polygon(
            generate_courtyard(
                uuid=_uuid('polygon-courtyard-{}'.format(key)),
                max_x=config.width / 2,
                max_y=config.length / 2,
                excess_x=COURTYARD_EXCESS,
                excess_y=COURTYARD_EXCESS,
            )
        )

        # Add name and value labels
        uuid_text_name = _uuid('text-name-{}'.format(key))
        uuid_text_value = _uuid('text-value-{}'.format(key))
        footprint.add_text(
            StrokeText(
                uuid=uuid_text_name,
                layer=Layer('top_names'),
                height=Height(1),
                stroke_width=StrokeWidth(0.2),
                letter_spacing=LetterSpacing.AUTO,
                line_spacing=LineSpacing.AUTO,
                align=Align('center bottom'),
                position=Position(0, config.length / 2 + LABEL_OFFSET),
                rotation=Rotation(0),
                auto_rotate=AutoRotate(True),
                mirror=Mirror(False),
                value=Value('{{NAME}}'),
            )
        )
        footprint.add_text(
            StrokeText(
                uuid=uuid_text_value,
                layer=Layer('top_values'),
                height=Height(1),
                stroke_width=StrokeWidth(0.2),
                letter_spacing=LetterSpacing.AUTO,
                line_spacing=LineSpacing.AUTO,
                align=Align('center top'),
                position=Position(0.0, -config.length / 2 - LABEL_OFFSET),
                rotation=Rotation(0.0),
                auto_rotate=AutoRotate(True),
                mirror=Mirror(False),
                value=Value('{{VALUE}}'),
            )
        )

    # Apply function to available footprints
    _generate_footprint('reflow', 'reflow', 0.0)
    _generate_footprint('hand-soldering', 'hand soldering', 0.3)

    # Generate 3D models
    uuid_3d = _uuid('3d')
    if generate_3d_models:
        generate_3d(full_name, uuid_pkg, uuid_3d, config, make_exposed)
    package.add_3d_model(Package3DModel(uuid_3d, Name(full_name)))
    for footprint in package.footprints:
        footprint.add_3d_model(Footprint3DModel(uuid_3d))

    # Save package
    package.serialize(path.join('out', config.library, category))
    return full_name


def generate_3d(
    full_name: str,
    uuid_pkg: str,
    uuid_3d: str,
    config: DfnConfig,
    make_exposed: bool,
) -> None:
    import cadquery as cq

    from cadquery_helpers import StepAssembly, StepColor

    print(f'Generating pkg 3D model "{full_name}": {uuid_3d}')

    dot_diameter = min(config.width * 0.2, 0.6)
    dot_position = min(config.width * 0.2, 0.8)
    dot_depth = 0.05
    dot_x = -(config.width / 2) + dot_position
    dot_y = (config.length / 2) - dot_position
    lead_standoff = 0.02
    lead_height = 0.2

    body = cq.Workplane('XY', origin=(0, 0, lead_standoff + (config.height_nominal / 2))).box(
        config.width, config.length, config.height_nominal
    )
    surface = cq.Workplane('back', origin=(0, 0, lead_standoff + config.height_nominal + 0.05))
    dot = surface.cylinder(0.5, dot_diameter / 2, centered=(True, True, False)).translate(
        (dot_x, dot_y, 0)
    )
    lead = cq.Workplane('ZY').box(lead_height, config.lead_width, config.lead_length)
    if make_exposed:
        exposed_lead = cq.Workplane('XY', origin=(0, 0, (lead_height / 2))).box(
            config.exposed_length, config.exposed_width, lead_height
        )

    if config.step_modification_fn:
        body, dot = config.step_modification_fn(body, dot, surface)

    body = body.cut(dot)

    assembly = StepAssembly(full_name)
    assembly.add_body(body, 'body', StepColor.IC_BODY)
    assembly.add_body(
        dot, 'dot', StepColor.IC_PIN1_DOT, location=cq.Location((0, 0, -0.05 - dot_depth))
    )
    pins_per_side = config.pin_count // 2
    for i in range(0, config.pin_count):
        side = -1 if (i < pins_per_side) else 1
        y1 = get_y(1 if (i < pins_per_side) else pins_per_side, pins_per_side, config.pitch, False)
        y_index = i % pins_per_side
        assembly.add_body(
            lead,
            'lead-{}'.format(i + 1),
            StepColor.LEAD_SMT,
            location=cq.Location(
                (
                    (((config.width - config.lead_length) / 2) + lead_standoff) * side,
                    y1 + y_index * config.pitch * side,
                    lead_height / 2,
                )
            ),
        )
    if make_exposed:
        assembly.add_body(exposed_lead, 'lead-exposed', StepColor.LEAD_SMT)

    # Save without fusing for massively better minification!
    out_path = path.join('out', config.library, 'pkg', uuid_pkg, f'{uuid_3d}.step')
    assembly.save(out_path, fused=False)


if __name__ == '__main__':
    if '--help' in sys.argv or '-h' in sys.argv:
        print(f'Usage: {sys.argv[0]} [--3d]')
        print()
        print('Options:')
        print('  --3d    Generate 3D models using cadquery')
        sys.exit(1)

    generate_3d_models = '--3d' in sys.argv
    if not generate_3d_models:
        warning = 'Note: Not generating 3D models unless the "--3d" argument is passed in!'
        print(f'\033[1;33m{warning}\033[0m')

    generated_packages: List[str] = []

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
                author='Hannes Badertscher',
                name='DFN{pitch}P{length}X{width}X{height}-{pin_count}',
                description='{pin_count}-pin Dual Flat No-Lead package (DFN), '
                'standardized by JEDEC MO-229F.\n\n'
                'Pitch: {pitch:.2f} mm\n'
                'Nominal width: {width:.2f} mm\n'
                'Nominal length: {length:.2f} mm\n'
                'Height: {height:.2f}mm',
                pkgcat='88cbb15c-2b69-4612-8764-c5d323f88f13',
                keywords='dfn,dual flat no-leads,mo-229f',
                config=config,
                make_exposed=make_exposed,
                generate_3d_models=generate_3d_models,
                create_date='2019-01-17T06:11:43Z',
            )
            if name not in generated_packages:
                generated_packages.append(name)
            else:
                print('Duplicate name found: {}'.format(name))

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
                author='Hannes Badertscher',
                name='DFN{pitch}P{length}X{width}X{height}-{pin_count}',
                description='{pin_count}-pin Dual Flat No-Lead package (DFN), '
                'Pitch: {pitch:.2f} mm\n'
                'Nominal width: {width:.2f} mm\n'
                'Nominal length: {length:.2f} mm\n'
                'Height: {height:.2f}mm',
                pkgcat='88cbb15c-2b69-4612-8764-c5d323f88f13',
                keywords='dfn,dual flat no-leads',
                config=config,
                make_exposed=make_exposed,
                generate_3d_models=generate_3d_models,
                create_date=config.create_date,
            )
            if name not in generated_packages:
                generated_packages.append(name)
            else:
                print('Duplicate name found: {}'.format(name))

    save_cache(uuid_cache_file, uuid_cache)
