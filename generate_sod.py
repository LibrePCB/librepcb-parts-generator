"""
Generate SOD diode packages
"""

import sys
from os import path
from uuid import uuid4

from typing import Dict, Iterable, Optional

from common import init_cache, now, save_cache
from entities.common import (
    Align,
    Angle,
    Author,
    Category,
    Created,
    Deprecated,
    Description,
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
    AlternativeName,
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

generator = 'librepcb-parts-generator (generate_sod.py)'

line_width = 0.2
line_width_thin = 0.15
pkg_text_height = 1.0
label_offset = 1.1
label_offset_thin = 0.8
silkscreen_clearance = 0.15
courtyard_excess = 0.25


# Initialize UUID cache
uuid_cache_file = 'uuid_cache_sod.csv'
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


class FootprintConfig:
    """
    Information about the footprint itself.

     L
    +--+   +--+
    |  | G |  | W
    +--+   +--+

    L = Length, W = Width, G = Gap

    """

    def __init__(
        self,
        key: str,
        name: str,
        pad_length: float,
        pad_width: float,
        pad_gap: float,
    ):
        self.key = key
        self.name = name
        self.pad_length = pad_length
        self.pad_width = pad_width
        self.pad_gap = pad_gap


class Config:
    def __init__(
        self,
        name: str,
        alternative_names: Iterable[AlternativeName],
        body_length: float,
        body_width: float,
        body_height: float,
        lead_span: float,
        lead_width: float,
        lead_contact_length: float,
        lead_thickness: float,
        footprints: Iterable[FootprintConfig],
        flat: bool,
        meta: Optional[Dict[str, str]] = None,  # Metadata that can be used in description
    ):
        self.name = name
        self.alternative_names = alternative_names
        self.body_length = body_length
        self.body_width = body_width
        self.body_height = body_height
        self.lead_span = lead_span
        self.lead_width = lead_width
        self.lead_contact_length = lead_contact_length
        self.lead_thickness = lead_thickness
        self.footprints = footprints
        self.flat = flat
        self.meta = meta


def generate_pkg(
    library: str,
    author: str,
    description: str,
    configs: Iterable[Config],
    generate_3d_models: bool,
    pkgcat: str,
    keywords: str,
    version: str,
    create_date: Optional[str],
) -> None:
    category = 'pkg'
    for config in configs:
        fmt_params_desc = {
            'lead_span': config.lead_span,
            'body_length': config.body_length,
            'body_width': config.body_width,
            'body_height': config.body_height,
            'meta': config.meta,
        }
        full_name = config.name  # Not generated due to non-standard rounding
        full_desc = description.format(**fmt_params_desc) + '\n\nGenerated with {}'.format(
            generator
        )
        full_keywords = ','.join(
            filter(
                None,
                [
                    keywords.format(**fmt_params_desc).lower(),
                ],
            )
        )

        def _uuid(identifier: str) -> str:
            return uuid(category, full_name, identifier)

        # UUIDs
        uuid_pkg = _uuid('pkg')
        uuid_pad_c = _uuid('pad-c')
        uuid_pad_a = _uuid('pad-a')

        print('Generating pkg "{}": {}'.format(full_name, uuid_pkg))

        package = Package(
            uuid=uuid_pkg,
            name=Name(full_name),
            description=Description(full_desc),
            keywords=Keywords(full_keywords),
            author=Author(author),
            version=Version(version),
            created=Created(create_date or now()),
            deprecated=Deprecated(False),
            generated_by=GeneratedBy(''),
            categories=[Category(pkgcat)],
            assembly_type=AssemblyType.SMT,
        )

        for alt_name in config.alternative_names:
            package.add_alternative_name(alt_name)

        package.add_pad(PackagePad(uuid_pad_c, Name('C')))
        package.add_pad(PackagePad(uuid_pad_a, Name('A')))

        def add_footprint_variant(fpt_config: FootprintConfig) -> None:
            uuid_footprint = _uuid('footprint-{}'.format(fpt_config.key))
            uuid_text_name = _uuid('text-name-{}'.format(fpt_config.key))
            uuid_text_value = _uuid('text-value-{}'.format(fpt_config.key))
            uuid_silkscreen = _uuid('polygon-silkscreen-{}'.format(fpt_config.key))
            uuid_outline = _uuid('polygon-outline-{}'.format(fpt_config.key))
            uuid_courtyard = _uuid('polygon-courtyard-{}'.format(fpt_config.key))
            uuid_lead_left = _uuid('polygon-lead-left-{}'.format(fpt_config.key))
            uuid_lead_right = _uuid('polygon-lead-right-{}'.format(fpt_config.key))
            uuid_body = _uuid('polygon-body-{}'.format(fpt_config.key))
            uuid_polarization_mark = _uuid('polygon-polarization-mark-{}'.format(fpt_config.key))

            # Line width adjusted for size of element
            if config.body_length >= 2.0:
                silk_lw = line_width
                doc_lw = line_width
            else:
                silk_lw = line_width_thin
                doc_lw = line_width_thin

            footprint = Footprint(
                uuid=uuid_footprint,
                name=Name(fpt_config.name),
                description=Description(''),
                position_3d=Position3D.zero(),
                rotation_3d=Rotation3D.zero(),
            )
            if 'Hand' in fpt_config.name:  # Added a bit hacky for new file format
                footprint.add_tag('hand-soldering')
            package.add_footprint(footprint)

            # Pads
            pad_dx = fpt_config.pad_gap / 2 + fpt_config.pad_length / 2  # x offset (delta-x)
            for p in [(uuid_pad_c, -1), (uuid_pad_a, 1)]:
                footprint.add_pad(
                    FootprintPad(
                        uuid=p[0],
                        side=ComponentSide.TOP,
                        shape=Shape.ROUNDED_RECT,
                        position=Position(p[1] * pad_dx, 0),
                        rotation=Rotation(0),
                        size=Size(fpt_config.pad_length, fpt_config.pad_width),
                        radius=ShapeRadius(0),
                        stop_mask=StopMaskConfig(StopMaskConfig.AUTO),
                        solder_paste=SolderPasteConfig.AUTO,
                        copper_clearance=CopperClearance(0.0),
                        function=PadFunction.STANDARD_PAD,
                        package_pad=PackagePadUuid(p[0]),
                        holes=[],
                    )
                )

            # Documentation
            dx = config.body_length / 2 - doc_lw / 2
            dy = config.body_width / 2 - doc_lw / 2
            footprint.add_polygon(
                Polygon(
                    uuid=uuid_body,
                    layer=Layer('top_documentation'),
                    width=Width(doc_lw),
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
            dx0 = config.lead_span / 2
            dx1 = config.body_length / 2
            dy = config.lead_width / 2
            for p_uuid, sign in [(uuid_lead_left, -1), (uuid_lead_right, 1)]:
                footprint.add_polygon(
                    Polygon(
                        uuid=p_uuid,
                        layer=Layer('top_documentation'),
                        width=Width(0),
                        fill=Fill(True),
                        grab_area=GrabArea(False),
                        vertices=[
                            Vertex(Position(dx0 * sign, dy), Angle(0)),
                            Vertex(Position(dx1 * sign, dy), Angle(0)),
                            Vertex(Position(dx1 * sign, -dy), Angle(0)),
                            Vertex(Position(dx0 * sign, -dy), Angle(0)),
                            Vertex(Position(dx0 * sign, dy), Angle(0)),
                        ],
                    )
                )
            dx_outer = ((config.body_length / 2) - doc_lw) * 0.75
            dx_inner = ((config.body_length / 2) - doc_lw) * 0.4
            dy = config.body_width / 2 - doc_lw
            footprint.add_polygon(
                Polygon(
                    uuid=uuid_polarization_mark,
                    layer=Layer('top_documentation'),
                    width=Width(0),
                    fill=Fill(True),
                    grab_area=GrabArea(True),
                    vertices=[
                        Vertex(Position(-dx_outer, dy), Angle(0)),
                        Vertex(Position(-dx_inner, dy), Angle(0)),
                        Vertex(Position(-dx_inner, -dy), Angle(0)),
                        Vertex(Position(-dx_outer, -dy), Angle(0)),
                        Vertex(Position(-dx_outer, dy), Angle(0)),
                    ],
                )
            )

            # Silkscreen
            x_left = -(pad_dx + fpt_config.pad_length / 2 + silk_lw / 2 + silkscreen_clearance)
            x_right = config.body_length / 2
            dy = max(
                config.body_width / 2 + silk_lw / 2,  # Based on body width
                fpt_config.pad_width / 2 + silk_lw / 2 + silkscreen_clearance,  # Based on pad width
            )
            footprint.add_polygon(
                Polygon(
                    uuid=uuid_silkscreen,
                    layer=Layer('top_legend'),
                    width=Width(silk_lw),
                    fill=Fill(False),
                    grab_area=GrabArea(False),
                    vertices=[
                        Vertex(Position(x_right, dy), Angle(0)),
                        Vertex(Position(x_left, dy), Angle(0)),
                        Vertex(Position(x_left, -dy), Angle(0)),
                        Vertex(Position(x_right, -dy), Angle(0)),
                    ],
                )
            )

            # Package outlines
            dx = config.body_length / 2
            dy = config.body_width / 2
            footprint.add_polygon(
                Polygon(
                    uuid=uuid_outline,
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
                    uuid=uuid_courtyard,
                    max_x=config.lead_span / 2,
                    max_y=config.body_width / 2,
                    excess_x=courtyard_excess,
                    excess_y=courtyard_excess,
                )
            )

            # Labels
            if config.body_width < 2.0:
                offset = label_offset_thin
            else:
                offset = label_offset
            dy = config.body_width / 2 + offset  # y offset (delta-y)
            footprint.add_text(
                StrokeText(
                    uuid=uuid_text_name,
                    layer=Layer('top_names'),
                    height=Height(pkg_text_height),
                    stroke_width=StrokeWidth(0.2),
                    letter_spacing=LetterSpacing.AUTO,
                    line_spacing=LineSpacing.AUTO,
                    align=Align('center bottom'),
                    position=Position(0.0, dy),
                    rotation=Rotation(0.0),
                    auto_rotate=AutoRotate(True),
                    mirror=Mirror(False),
                    value=Value('{{NAME}}'),
                )
            )
            footprint.add_text(
                StrokeText(
                    uuid=uuid_text_value,
                    layer=Layer('top_values'),
                    height=Height(pkg_text_height),
                    stroke_width=StrokeWidth(0.2),
                    letter_spacing=LetterSpacing.AUTO,
                    line_spacing=LineSpacing.AUTO,
                    align=Align('center top'),
                    position=Position(0.0, -dy),
                    rotation=Rotation(0.0),
                    auto_rotate=AutoRotate(True),
                    mirror=Mirror(False),
                    value=Value('{{VALUE}}'),
                )
            )

        for fpt in config.footprints:
            add_footprint_variant(fpt)

        # Generate 3D model
        uuid_3d = uuid('pkg', full_name, '3d')
        if generate_3d_models:
            generate_3d(library, full_name, uuid_pkg, uuid_3d, config)
        package.add_3d_model(Package3DModel(uuid_3d, Name(full_name)))
        for footprint in package.footprints:
            footprint.add_3d_model(Footprint3DModel(uuid_3d))

        package.serialize(path.join('out', library, category))


def generate_3d(
    library: str,
    full_name: str,
    uuid_pkg: str,
    uuid_3d: str,
    config: Config,
) -> None:
    import cadquery as cq

    from cadquery_helpers import StepAssembly, StepColor

    print(f'Generating pkg 3D model "{full_name}": {uuid_3d}')

    body_standoff = 0 if config.flat else 0.05
    body_height = config.body_height - body_standoff
    body_chamfer = 0.05
    leg_z_top = body_standoff + (body_height / 2)
    bend_radius = 0 + (config.lead_thickness / 2)
    marking_width = config.body_length * 0.2
    marking_pos = config.body_length * 0.25

    body = (
        cq.Workplane('XY', origin=(0, 0, body_standoff + (body_height / 2)))
        .box(config.body_length, config.body_width, body_height)
        .edges()
        .chamfer(body_chamfer)
    )
    marking = cq.Workplane('XY', origin=(-marking_pos, 0, body_standoff + body_height)).box(
        marking_width, config.body_width - 2 * body_chamfer, 0.05
    )
    if config.flat:
        leg = cq.Workplane('XY', origin=(0, 0, config.lead_thickness / 2)).box(
            config.lead_span, config.lead_width, config.lead_thickness
        )
    else:
        leg_path = (
            cq.Workplane('XZ')
            .hLine(config.lead_contact_length - (config.lead_thickness / 2) - bend_radius)
            .ellipseArc(x_radius=bend_radius, y_radius=bend_radius, angle1=270, angle2=360, sense=1)
            .vLine(leg_z_top - config.lead_thickness - (2 * bend_radius))
            .ellipseArc(x_radius=bend_radius, y_radius=bend_radius, angle1=90, angle2=180, sense=-1)
            .hLine(
                config.lead_span
                - (2 * bend_radius)
                - (2 * config.lead_contact_length)
                + config.lead_thickness
            )
            .ellipseArc(x_radius=bend_radius, y_radius=bend_radius, angle1=0, angle2=90, sense=-1)
            .vLine(-(leg_z_top - config.lead_thickness - (2 * bend_radius)))
            .ellipseArc(x_radius=bend_radius, y_radius=bend_radius, angle1=180, angle2=270, sense=1)
            .hLine(config.lead_contact_length - (config.lead_thickness / 2) - bend_radius)
        )
        leg = (
            cq.Workplane('ZY')
            .rect(config.lead_thickness, config.lead_width)
            .sweep(leg_path)
            .translate((-config.lead_span / 2, 0, 0))
        )

    assembly = StepAssembly(full_name)
    assembly.add_body(body, 'body', StepColor.IC_BODY)
    assembly.add_body(marking, 'marking', StepColor.IC_PIN1_DOT)
    assembly.add_body(leg, 'legs', StepColor.LEAD_SMT)

    out_path = path.join('out', library, 'pkg', uuid_pkg, f'{uuid_3d}.step')
    assembly.save(out_path, fused=True)


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

    generate_pkg(
        library='LibrePCB_Base.lplib',
        author='Danilo B., U. Bruhin',
        description='Small outline diode (JEDEC {meta[jedec]}).\n\n'
        'Lead span: {lead_span}\n'
        'Body length: {body_length}mm\n'
        'Body width: {body_width}mm\n'
        'Max height: {body_height}mm',
        configs=[
            # https://www.diodes.com/assets/Package-Files/SOD123.pdf
            Config(
                'SOD3717X135',
                [AlternativeName('SOD-123', 'JEDEC')],
                2.65,
                1.55,
                1.05,
                3.65,
                0.57,
                0.3,
                0.11,
                [
                    FootprintConfig('default', 'default', 0.9, 0.95, 2.25),
                    FootprintConfig('handsolder', 'Hand Soldering', 1.5, 0.95, 2.25),
                ],
                False,
                meta={'jedec': 'SOD-123', 'keywords': 'SOD123'},
            ),
            # https://www.diodes.com/assets/Package-Files/SOD323.pdf
            Config(
                'SOD2514X110',
                [AlternativeName('SOD-323', 'JEDEC')],
                1.7,
                1.3,
                1.05,
                2.5,
                0.3,
                0.3,
                0.11,
                [
                    FootprintConfig('default', 'default', 0.6, 0.45, 1.51),
                    FootprintConfig('handsolder', 'Hand Soldering', 1.0, 0.45, 1.51),
                ],
                False,
                meta={'jedec': 'SOD-323', 'keywords': 'SOD323'},
            ),
            # https://www.diodes.com/assets/Package-Files/SOD523.pdf
            Config(
                'SOD1709X65',
                [AlternativeName('SOD-523', 'JEDEC')],
                1.2,
                0.8,
                0.6,
                1.65,
                0.3,
                0.3,
                0.14,
                [
                    FootprintConfig('default', 'default', 0.6, 0.7, 0.8),
                    FootprintConfig('handsolder', 'Hand Soldering', 1.0, 0.7, 0.8),
                ],
                True,
                meta={'jedec': 'SOD-523', 'keywords': 'SOD523'},
            ),
        ],
        generate_3d_models=generate_3d_models,
        pkgcat='9b31c9b4-04b6-4f97-ad12-f095d196bd38',
        keywords='{meta[jedec]},{meta[keywords]},small outline diode',
        version='0.2',
        create_date='2018-12-02T22:17:40Z',
    )
    save_cache(uuid_cache_file, uuid_cache)
