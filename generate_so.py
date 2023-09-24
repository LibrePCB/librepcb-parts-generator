"""
Generate the following SO packages:

- SOIC (both EIAJ and JEDEC)
- TSSOP (JEDEC MO-153)
- SSOP (JEDEC MO-150 and MO-152)
- TSOP (JEDEC MS-024)

"""
import sys
from os import path
from uuid import uuid4

from typing import Dict, Iterable, List, Optional

from common import format_ipc_dimension as fd
from common import init_cache, now, save_cache
from entities.common import (
    Align, Angle, Author, Category, Circle, Created, Deprecated, Description, Diameter, Fill, GeneratedBy, GrabArea,
    Height, Keywords, Layer, Name, Polygon, Position, Position3D, Rotation, Rotation3D, Value, Version, Vertex, Width,
    generate_courtyard
)
from entities.package import (
    AssemblyType, AutoRotate, ComponentSide, CopperClearance, Footprint, Footprint3DModel, FootprintPad, LetterSpacing,
    LineSpacing, Mirror, Package, Package3DModel, PackagePad, PackagePadUuid, PadFunction, Shape, ShapeRadius, Size,
    SolderPasteConfig, StopMaskConfig, StrokeText, StrokeWidth
)

generator = 'librepcb-parts-generator (generate_so.py)'

line_width = 0.25
pkg_text_height = 1.0
silkscreen_offset = 0.150  # 150 µm
pin_package_offset = 0.762  # Distance between pad center and the package body


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
    library: str,
    author: str,
    name: str,
    description: str,
    configs: Iterable[SoConfig],
    lead_width_lookup: Dict[float, float],
    lead_contact_length: float,
    generate_3d_models: bool,
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
        ) + "\n\nGenerated with {}".format(generator)

        def _uuid(identifier: str) -> str:
            return uuid(category, full_name, identifier)

        uuid_pkg = _uuid('pkg')
        uuid_pads = [_uuid('pad-{}'.format(p)) for p in range(1, pin_count + 1)]
        uuid_leads1 = [_uuid('lead-contact-{}'.format(p)) for p in range(1, pin_count + 1)]
        uuid_leads2 = [_uuid('lead-proj-{}'.format(p)) for p in range(1, pin_count + 1)]

        print('Generating {}: {}'.format(full_name, uuid_pkg))

        package = Package(
            uuid=uuid_pkg,
            name=Name(full_name),
            description=Description(full_description),
            keywords=Keywords("soic{},so{},{}".format(pin_count, pin_count, keywords)),
            author=Author(author),
            version=Version(version),
            created=Created(create_date or now()),
            deprecated=Deprecated(False),
            generated_by=GeneratedBy(''),
            categories=[Category(pkgcat)],
            assembly_type=AssemblyType.SMT,
        )

        for p in range(1, pin_count + 1):
            package.add_pad(PackagePad(uuid_pads[p - 1], Name(str(p))))

        def add_footprint_variant(
            key: str,
            name: str,
            density_level: str,
        ) -> None:
            uuid_footprint = _uuid('footprint-{}'.format(key))
            uuid_silkscreen_top = _uuid('polygon-silkscreen-{}'.format(key))
            uuid_silkscreen_bot = _uuid('polygon-silkscreen2-{}'.format(key))
            uuid_body = _uuid('polygon-body-{}'.format(key))
            uuid_pin1_dot = _uuid('pin1-dot-{}'.format(key))
            uuid_outline = _uuid('polygon-outline-{}'.format(key))
            uuid_courtyard = _uuid('polygon-courtyard-{}'.format(key))
            uuid_text_name = _uuid('text-name-{}'.format(key))
            uuid_text_value = _uuid('text-value-{}'.format(key))

            # Max boundaries (pads or body)
            max_x = 0.0
            max_y = 0.0

            # Max boundaries (copper only)
            max_y_copper = 0.0

            footprint = Footprint(
                uuid=uuid_footprint,
                name=Name(name),
                description=Description(''),
                position_3d=Position3D.zero(),
                rotation_3d=Rotation3D.zero(),
            )
            package.add_footprint(footprint)

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
                    pxo = -pad_x_offset
                else:
                    y = -get_y(p - mid, pin_count // 2, pitch, False)
                    pxo = pad_x_offset
                pad_uuid = uuid_pads[p - 1]
                footprint.add_pad(FootprintPad(
                    uuid=pad_uuid,
                    side=ComponentSide.TOP,
                    shape=Shape.ROUNDED_RECT,
                    position=Position(pxo, y),
                    rotation=Rotation(0),
                    size=Size(pad_length, pad_width),
                    radius=ShapeRadius(0.5),
                    stop_mask=StopMaskConfig.AUTO,
                    solder_paste=SolderPasteConfig.AUTO,
                    copper_clearance=CopperClearance(0.0),
                    function=PadFunction.STANDARD_PAD,
                    package_pad=PackagePadUuid(pad_uuid),
                    holes=[],
                ))
                max_y_copper = max(max_y_copper, y + pad_width / 2)
            max_x = max(max_x, total_width / 2 + pad_toe)

            # Documentation: Leads
            lead_contact_x_offset = total_width / 2 - lead_contact_length  # this is the inner side of the contact area
            for p in range(1, pin_count + 1):
                mid = pin_count // 2
                if p <= mid:  # left side
                    y = get_y(p, pin_count // 2, pitch, False)
                    lcxo_max = -lead_contact_x_offset - lead_contact_length
                    lcxo_min = -lead_contact_x_offset
                    body_side = -body_width / 2
                else:  # right side
                    y = -get_y(p - mid, pin_count // 2, pitch, False)
                    lcxo_min = lead_contact_x_offset
                    lcxo_max = lead_contact_x_offset + lead_contact_length
                    body_side = body_width / 2
                y_max = y - lead_width / 2
                y_min = y + lead_width / 2
                lead_uuid_ctct = uuid_leads1[p - 1]  # Contact area
                lead_uuid_proj = uuid_leads2[p - 1]  # Vertical projection
                # Contact area
                footprint.add_polygon(Polygon(
                    uuid=lead_uuid_ctct,
                    layer=Layer('top_documentation'),
                    width=Width(0),
                    fill=Fill(True),
                    grab_area=GrabArea(False),
                    vertices=[
                        Vertex(Position(lcxo_min, y_max), Angle(0)),
                        Vertex(Position(lcxo_max, y_max), Angle(0)),
                        Vertex(Position(lcxo_max, y_min), Angle(0)),
                        Vertex(Position(lcxo_min, y_min), Angle(0)),
                        Vertex(Position(lcxo_min, y_max), Angle(0)),
                    ],
                ))
                # Vertical projection, between contact area and body
                footprint.add_polygon(Polygon(
                    uuid=lead_uuid_proj,
                    layer=Layer('top_documentation'),
                    width=Width(0),
                    fill=Fill(True),
                    grab_area=GrabArea(False),
                    vertices=[
                        Vertex(Position(body_side, y_max), Angle(0)),
                        Vertex(Position(lcxo_min, y_max), Angle(0)),
                        Vertex(Position(lcxo_min, y_min), Angle(0)),
                        Vertex(Position(body_side, y_min), Angle(0)),
                        Vertex(Position(body_side, y_max), Angle(0)),
                    ],
                ))

            # Silkscreen (fully outside body)
            # Ensure minimum clearance between copper and silkscreen
            y_offset = max(silkscreen_offset - (body_length / 2 - max_y_copper), 0)
            y_max = body_length / 2 + line_width / 2 + y_offset
            y_min = -body_length / 2 - line_width / 2 - y_offset
            short_x_offset = body_width / 2 - line_width / 2
            long_x_offset = total_width / 2 - line_width / 2 + pad_toe  # Pin1 marking
            footprint.add_polygon(Polygon(
                uuid=uuid_silkscreen_top,
                layer=Layer('top_legend'),
                width=Width(line_width),
                fill=Fill(False),
                grab_area=GrabArea(False),
                vertices=[
                    Vertex(Position(-long_x_offset, y_max), Angle(0)),
                    Vertex(Position(short_x_offset, y_max), Angle(0)),
                ],
            ))
            footprint.add_polygon(Polygon(
                uuid=uuid_silkscreen_bot,
                layer=Layer('top_legend'),
                width=Width(line_width),
                fill=Fill(False),
                grab_area=GrabArea(False),
                vertices=[
                    Vertex(Position(-short_x_offset, y_min), Angle(0)),
                    Vertex(Position(short_x_offset, y_min), Angle(0)),
                ],
            ))

            # Documentation body
            body_x_offset = body_width / 2 - line_width / 2
            y_max = body_length / 2 - line_width / 2
            y_min = -body_length / 2 + line_width / 2
            oxo = body_x_offset  # Used for shorter code lines below :)
            footprint.add_polygon(Polygon(
                uuid=uuid_body,
                layer=Layer('top_documentation'),
                width=Width(line_width),
                fill=Fill(False),
                grab_area=GrabArea(True),
                vertices=[
                    Vertex(Position(-oxo, y_max), Angle(0)),
                    Vertex(Position(oxo, y_max), Angle(0)),
                    Vertex(Position(oxo, y_min), Angle(0)),
                    Vertex(Position(-oxo, y_min), Angle(0)),
                    Vertex(Position(-oxo, y_max), Angle(0)),
                ],
            ))
            max_y = max(max_y, body_length / 2)  # Body contour

            # Documentation: Pin 1 dot
            pin1_dot_diameter = 0.5
            pin1_dot_offset = 1.0
            dx = body_width / 2 - pin1_dot_offset
            dy = config.body_length / 2 - pin1_dot_offset
            pin1_dot = Circle(
                uuid_pin1_dot,
                Layer('top_documentation'),
                Width(0.0),
                Fill(True),
                GrabArea(False),
                Diameter(pin1_dot_diameter),
                Position(-dx, dy),
            )
            footprint.add_circle(pin1_dot)

            # Package Outline
            dx = config.total_width / 2
            dy = config.body_length / 2
            footprint.add_polygon(Polygon(
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
            ))

            # Courtyard
            courtyard_excess = get_by_density(pitch, density_level, 'courtyard')
            footprint.add_polygon(generate_courtyard(
                uuid=uuid_courtyard,
                max_x=max_x,
                max_y=max_y,
                excess_x=courtyard_excess,
                excess_y=courtyard_excess,
            ))

            # Labels
            y_max = body_length / 2 + 1.27
            y_min = -body_length / 2 - 1.27
            footprint.add_text(StrokeText(
                uuid=uuid_text_name,
                layer=Layer('top_names'),
                height=Height(pkg_text_height),
                stroke_width=StrokeWidth(0.2),
                letter_spacing=LetterSpacing.AUTO,
                line_spacing=LineSpacing.AUTO,
                align=Align('center bottom'),
                position=Position(0.0, y_max),
                rotation=Rotation(0.0),
                auto_rotate=AutoRotate(True),
                mirror=Mirror(False),
                value=Value('{{NAME}}'),
            ))
            footprint.add_text(StrokeText(
                uuid=uuid_text_value,
                layer=Layer('top_values'),
                height=Height(pkg_text_height),
                stroke_width=StrokeWidth(0.2),
                letter_spacing=LetterSpacing.AUTO,
                line_spacing=LineSpacing.AUTO,
                align=Align('center top'),
                position=Position(0.0, y_min),
                rotation=Rotation(0.0),
                auto_rotate=AutoRotate(True),
                mirror=Mirror(False),
                value=Value('{{VALUE}}'),
            ))

        add_footprint_variant('density~b', 'Density Level B (median protrusion)', 'B')
        add_footprint_variant('density~a', 'Density Level A (max protrusion)', 'A')
        add_footprint_variant('density~c', 'Density Level C (min protrusion)', 'C')

        # Generate 3D models (for certain package types)
        uuid_3d = uuid('pkg', full_name, '3d')
        if generate_3d_models:
            generate_3d(library, full_name, uuid_pkg, uuid_3d, config,
                        lead_width, lead_contact_length)
        package.add_3d_model(Package3DModel(uuid_3d, Name(full_name)))
        for footprint in package.footprints:
            footprint.add_3d_model(Footprint3DModel(uuid_3d))

        package.serialize(path.join('out', library, category))


def generate_3d(
    library: str,
    full_name: str,
    uuid_pkg: str,
    uuid_3d: str,
    config: SoConfig,
    lead_width: float,
    lead_contact_length: float,
) -> None:
    import cadquery as cq

    from cadquery_helpers import StepAssembly, StepColor

    print(f'Generating pkg 3D model "{full_name}": {uuid_3d}')

    body_standoff = 0.1
    body_height = config.height - body_standoff
    body_chamfer = 0.15
    dot_diameter = 0.8
    dot_position = 1.0
    dot_depth = 0.15
    leg_height = 0.17
    leg_z_top = body_standoff + (body_height / 2)
    bend_radius = 0.1 + (leg_height / 2)

    dot_center = (
        -(config.body_width / 2) + dot_position,
        (config.body_length / 2) - dot_position,
        body_standoff + body_height - dot_depth
    )

    body = cq.Workplane('XY', origin=(0, 0, body_standoff + (body_height / 2))) \
        .box(config.body_width, config.body_length, body_height) \
        .edges().chamfer(body_chamfer) \
        .workplane(origin=(dot_center[0], dot_center[1]), offset=(body_height / 2) - dot_depth) \
        .cylinder(5, dot_diameter / 2, centered=(True, True, False), combine='cut')
    dot = cq.Workplane('XY', origin=dot_center) \
        .cylinder(0.05, dot_diameter / 2, centered=(True, True, False))
    leg_path = cq.Workplane("XZ") \
        .hLine(lead_contact_length - (leg_height / 2) - bend_radius) \
        .ellipseArc(x_radius=bend_radius, y_radius=bend_radius, angle1=270, angle2=360, sense=1) \
        .vLine(leg_z_top - leg_height - (2 * bend_radius)) \
        .ellipseArc(x_radius=bend_radius, y_radius=bend_radius, angle1=90, angle2=180, sense=-1) \
        .hLine(config.total_width - (2 * bend_radius) - (2 * lead_contact_length) + leg_height) \
        .ellipseArc(x_radius=bend_radius, y_radius=bend_radius, angle1=0, angle2=90, sense=-1) \
        .vLine(-(leg_z_top - leg_height - (2 * bend_radius))) \
        .ellipseArc(x_radius=bend_radius, y_radius=bend_radius, angle1=180, angle2=270, sense=1) \
        .hLine(lead_contact_length - (leg_height / 2) - bend_radius)
    leg = cq.Workplane("ZY") \
        .rect(leg_height, lead_width) \
        .sweep(leg_path)

    assembly = StepAssembly(full_name)
    assembly.add_body(body, 'body', StepColor.IC_BODY)
    assembly.add_body(dot, 'dot', StepColor.IC_PIN1_DOT)
    y1 = get_y(1, config.pin_count // 2, config.pitch, False)
    for i in range(0, config.pin_count // 2):
        assembly.add_body(
            leg,
            'leg-{}'.format(i + 1), StepColor.LEAD_SMT,
            location=cq.Location((
                -config.total_width / 2,
                y1 - i * config.pitch,
                leg_height / 2,
            ))
        )

    # Save without fusing for massively better minification!
    out_path = path.join('out', library, 'pkg', uuid_pkg, f'{uuid_3d}.step')
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

    # SOIC
    configs = []  # type: List[SoConfig]
    for pin_count in [6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 28, 30, 32]:
        for height in [1.2, 1.4, 1.7, 2.7]:
            pitch = 1.27
            body_length = (pin_count / 2 - 1) * pitch + 2.0
            body_width = 5.22
            total_width = 8.42  # effective, not nominal (7.62)
            configs.append(SoConfig(pin_count, pitch, body_length, body_width, total_width, height))
    generate_pkg(
        library='LibrePCB_Base.lplib',
        author='Danilo B.',
        name='SOIC{pitch}P762X{height}-{pin_count}',
        description='{pin_count}-pin Small Outline Integrated Circuit (SOIC), '
                    'standardized by EIAJ.\n\n'
                    'Pitch: {pitch:.2f} mm\nNominal width: 7.62mm\nHeight: {height:.2f}mm',
        configs=configs,
        lead_width_lookup={1.27: 0.4},
        lead_contact_length=0.8,
        generate_3d_models=generate_3d_models,
        pkgcat='a074fabf-4912-4c29-bc6b-451bf43c2193',
        keywords='so,soic,small outline,smd,eiaj',
        version='0.3',
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
        library='LibrePCB_Base.lplib',
        author='Danilo B.',
        name='SOIC{pitch}P1524X{height}-{pin_count}',
        description='{pin_count}-pin Small Outline Integrated Circuit (SOIC), '
                    'standardized by EIAJ.\n\n'
                    'Pitch: {pitch:.2f} mm\nNominal width: 15.24mm\nHeight: {height:.2f}mm',
        configs=configs,
        lead_width_lookup={1.27: 0.4},
        lead_contact_length=0.8,
        generate_3d_models=generate_3d_models,
        pkgcat='a074fabf-4912-4c29-bc6b-451bf43c2193',
        keywords='so,soic,small outline,smd,eiaj',
        version='0.3',
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
        library='LibrePCB_Base.lplib',
        author='Danilo B.',
        name='SOIC{pitch}P600X{height}-{pin_count}',
        description='{pin_count}-pin Small Outline Integrated Circuit (SOIC), '
                    'standardized by JEDEC (MS-012G).\n\n'
                    'Pitch: {pitch:.2f} mm\nNominal width: 6.00mm\nHeight: {height:.2f}mm',
        configs=configs,
        lead_width_lookup={1.27: 0.45},
        lead_contact_length=0.835,
        generate_3d_models=generate_3d_models,
        pkgcat='a074fabf-4912-4c29-bc6b-451bf43c2193',
        keywords='so,soic,small outline,smd,jedec',
        version='0.3',
        create_date='2018-11-10T20:32:03Z',
    )
    configs = []
    for pin_count in [14, 16, 18, 20, 24, 28]:
        pitch = 1.27
        height = 2.65
        body_length = (pin_count / 2 - 1) * pitch + 1.6
        body_width = 7.5
        total_width = 10.3
        configs.append(SoConfig(pin_count, pitch, body_length, body_width, total_width, height))
    generate_pkg(
        library='LibrePCB_Base.lplib',
        author='U. Bruhin',
        name='SOIC{pitch}P1030X{height}-{pin_count}',
        description='{pin_count}-pin Small Outline Integrated Circuit (SOIC), '
                    'standardized by JEDEC (MS-013F).\n\n'
                    'Pitch: {pitch:.2f} mm\nNominal width: 10.30mm\nHeight: {height:.2f}mm',
        configs=configs,
        lead_width_lookup={1.27: 0.45},
        lead_contact_length=0.835,
        generate_3d_models=generate_3d_models,
        pkgcat='a074fabf-4912-4c29-bc6b-451bf43c2193',
        keywords='so,soic,small outline,smd,jedec,ms-013f',
        version='0.2',
        create_date='2020-09-15T20:46:13Z',
    )

    # TSSOP
    generate_pkg(
        library='LibrePCB_Base.lplib',
        author='Danilo B.',
        # Name according to IPC7351C
        name='TSSOP{pin_count}P{pitch}_{body_length}X{lead_span}X{height}L{lead_length}X{lead_width}',
        description='{pin_count}-pin Thin-Shrink Small Outline Package (TSSOP), '
                    'standardized by JEDEC (MO-153), variation {variation}.\n\n'
                    'Pitch: {pitch:.2f} mm\nBody length: {body_length:.2f} mm\n'
                    'Body width: {body_width:.2f} mm\nLead span: {lead_span:.2f} mm\n'
                    'Height: {height:.2f} mm\n'
                    'Lead length: {lead_length:.2f} mm\nLead width: {lead_width:.2f} mm',
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
        generate_3d_models=generate_3d_models,
        pkgcat='241d9d5d-8f74-4740-8901-3cf51cf50091',
        keywords='so,sop,tssop,small outline package,smd',
        version='0.3',
        create_date='2019-06-16T12:46:54Z',
    )

    # SSOP
    generate_pkg(
        library='LibrePCB_Base.lplib',
        author='Danilo B.',
        # Name according to IPC7351C
        name='SSOP{pin_count}P{pitch}_{body_length}X{lead_span}X{height}L{lead_length}X{lead_width}',
        description='{pin_count}-pin Plastic Shrink Small Outline Package (SSOP), '
                    'standardized by JEDEC (MO-152), variation {variation}.\n\n'
                    'Pitch: {pitch:.2f} mm\nBody length: {body_length:.2f} mm\n'
                    'Body width: {body_width:.2f} mm\nLead span: {lead_span:.2f} mm\n'
                    'Height: {height:.2f} mm\n'
                    'Lead length: {lead_length:.2f} mm\nLead width: {lead_width:.2f} mm',
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
        generate_3d_models=generate_3d_models,
        pkgcat='3627bf02-2e6e-4d68-9ada-743fa69a4f8c',
        keywords='so,sop,ssop,small outline package,smd,jedec,mo-152',
        version='0.2',
        create_date='2019-07-21T12:55:20Z',
    )
    generate_pkg(
        library='LibrePCB_Base.lplib',
        author='Danilo B.',
        # Name according to IPC7351C
        name='SSOP{pin_count}P{pitch}_{body_length}X{lead_span}X{height}L{lead_length}X{lead_width}',
        description='{pin_count}-pin Plastic Shrink Small Outline Package (SSOP), '
                    'standardized by JEDEC (MO-150), variation {variation}.\n\n'
                    'Pitch: {pitch:.2f} mm\nBody length: {body_length:.2f} mm\n'
                    'Body width: {body_width:.2f} mm\nLead span: {lead_span:.2f} mm\n'
                    'Height: {height:.2f} mm\n'
                    'Lead length: {lead_length:.2f} mm\nLead width: {lead_width:.2f} mm',
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
        generate_3d_models=generate_3d_models,
        pkgcat='3627bf02-2e6e-4d68-9ada-743fa69a4f8c',
        keywords='so,sop,ssop,small outline package,smd,jedec,mo-150',
        version='0.2',
        create_date='2019-07-21T12:55:20Z',
    )

    # TSOP
    generate_pkg(
        library='LibrePCB_Base.lplib',
        author='Tubbles',
        # Name extrapolated from IPC7351C
        name='TSOP{pin_count}P{pitch}_{body_length}X{lead_span}X{height}L{lead_length}X{lead_width}',
        description='{pin_count}-pin Thin Small Outline Package (TSOP), '
                    'standardized by JEDEC (MS-024), Type II (pins on longer side), variation {variation}.\n\n'
                    'Pitch: {pitch:.2f} mm\nBody length: {body_length:.2f} mm\n'
                    'Body width: {body_width:.2f} mm\nLead span: {lead_span:.2f} mm\n'
                    'Height: {height:.2f} mm\n'
                    'Lead length: {lead_length:.2f} mm\nLead width: {lead_width:.2f} mm',
        configs=[
            # pin count, pitch, body length, body width, total width, height

            # Symbols based on JEDEC MS-024:
            #        N    e     D      E1     E      A
            SoConfig(28,  1.27, 18.41, 10.16, 11.76, 1.2, 'AA'),
            SoConfig(32,  1.27, 20.95, 10.16, 11.76, 1.2, 'BA'),
            SoConfig(50,  0.80, 20.95, 10.16, 11.76, 1.2, 'BC'),
            SoConfig(80,  0.50, 20.95, 10.16, 11.76, 1.2, 'BD'),
            SoConfig(36,  1.27, 23.49, 10.16, 11.76, 1.2, 'CA'),
            SoConfig(70,  0.65, 23.49, 10.16, 11.76, 1.2, 'CB'),
            SoConfig(40,  1.27, 26.03, 10.16, 11.76, 1.2, 'DA'),
            SoConfig(70,  0.80, 28.57, 10.16, 11.76, 1.2, 'EA'),
            SoConfig(54,  0.80, 22.22, 10.16, 11.76, 1.2, 'FA'),
            SoConfig(86,  0.50, 22.22, 10.16, 11.76, 1.2, 'FB'),
            SoConfig(66,  0.65, 22.22, 10.16, 11.76, 1.2, 'FC'),
            SoConfig(54,  0.40, 11.20, 10.16, 11.76, 1.2, 'GA'),
        ],
        lead_width_lookup={
            0.40: 0.18,
            0.50: 0.22,
            0.65: 0.30,
            0.80: 0.375,
            1.27: 0.41,
        },
        lead_contact_length=0.5,
        generate_3d_models=generate_3d_models,
        pkgcat='7993abb0-fb0a-4157-8f83-1db890755836',
        keywords='so,sop,tsop,small outline package,smd',
        version='0.2',
        create_date='2020-12-26T16:14:30Z',
    )
    save_cache(uuid_cache_file, uuid_cache)
