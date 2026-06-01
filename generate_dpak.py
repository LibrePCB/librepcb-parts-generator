"""
Generate the DPAK packages according to JEDEC TO-252.
"""

import math
import sys
from collections import namedtuple
from dataclasses import dataclass
from os import path
from uuid import uuid4

from typing import Dict, Iterable, List, Optional, cast

from common import format_ipc_dimension as fd
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

generator = 'librepcb-parts-generator (generate_dpak.py)'

LINE_WIDTH = 0.2
TEXT_HEIGHT = 1.0
LEGEND_OFFSET = 0.150  # 150 µm

# Footprint Expert Guidelines mentions that two separate courtyard values may
# be used for body/leads vs. pads, while by default they are assumed to be
# equal. I think this would lead to too much courtyard, so I'd suggest to use
# a minimal courtyard of 0.1mm around pads.
COURTYARD_AROUND_PADS = 0.1  # 100 µm

# Based on Footprint Expert Guidelines, Chapter 7.0 (Nominal Calculation)
Excess = namedtuple('Excess', 'toe heel side courtyard')
DENSITY_LEVELS: List[Dict[str, object]] = [
    {
        'pitch_above': 2.54,
        'C': Excess(0.35, 0.50, 0.15, 0.10),
        'B': Excess(0.45, 0.60, 0.25, 0.20),
        'A': Excess(0.55, 0.70, 0.30, 0.40),
    },
    {
        'pitch_above': 2.28,
        'C': Excess(0.35, 0.50, 0.10, 0.10),
        'B': Excess(0.45, 0.60, 0.20, 0.20),
        'A': Excess(0.55, 0.70, 0.25, 0.40),
    },
    {
        'pitch_above': 1.70,
        'C': Excess(0.25, 0.50, 0.05, 0.10),
        'B': Excess(0.35, 0.60, 0.15, 0.20),
        'A': Excess(0.45, 0.70, 0.20, 0.40),
    },
    {
        'pitch_above': 1.27,
        'C': Excess(0.20, 0.45, 0.00, 0.10),
        'B': Excess(0.30, 0.55, 0.10, 0.20),
        'A': Excess(0.40, 0.65, 0.15, 0.40),
    },
    {
        'pitch_above': 0.0,
        'C': Excess(0.15, 0.40, 0.00, 0.10),
        'B': Excess(0.25, 0.50, 0.10, 0.20),
        'A': Excess(0.35, 0.60, 0.15, 0.40),
    },
]
# Flat Lug / DPAK Tab
TAB_DENSITY_LEVELS: Dict[str, Excess] = {
    'C': Excess(0.25, 0.02, 0.02, 0.10),
    'B': Excess(0.40, 0.05, 0.05, 0.20),
    'A': Excess(0.55, 0.08, 0.08, 0.40),
}


# Initialize UUID cache
uuid_cache_file = 'uuid_cache_dpak.csv'
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


def excess_by_density(pitch: float, level: str) -> Excess:
    for table in DENSITY_LEVELS:
        if pitch > cast(float, table['pitch_above']):
            return cast(Excess, table[level])
    assert False


@dataclass(frozen=True)
class Config:
    variation: str
    pin_count: int  # including the thermal tab
    pitch: float
    body_size_x: float
    body_size_y: float
    body_size_z: float
    tab_size_x: float
    tab_size_y: float
    tab_size_z: float
    tab_overhang: float
    lead_span: float
    lead_contact_length: float
    lead_width: float
    min_thermal_size_y: float
    thermal_solder_paste_rows: int
    thermal_solder_paste_coverage: float
    alternative_names: Iterable[AlternativeName]

    @property
    def tab_pin_number(self) -> int:
        assert (self.pin_count % 2) == 1
        return (self.pin_count + 1) // 2

    @property
    def lead_length(self) -> float:
        return self.lead_span - self.tab_overhang - self.body_size_x

    @property
    def pin1_y(self) -> float:
        return ((self.pin_count - 1) * self.pitch) / 2


def generate_pkg(
    library: str,
    author: str,
    name: str,
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
        assert (config.pin_count % 2) == 1  # Only implemented for odd pin counts!
        assert config.pin_count == 3  # Not tested for other pin counts yet!
        min_x = config.body_size_x / 2 + config.tab_overhang - config.lead_span
        max_x = config.body_size_x / 2 + config.tab_overhang

        full_name = name.format(
            pin_count=config.pin_count,
            pitch=fd(config.pitch),
            body_size_y=fd(config.body_size_y),
            body_size_z=fd(config.body_size_z),
            tab_size_x=fd(config.tab_size_x),
            tab_size_y=fd(config.tab_size_y),
            lead_span=fd(config.lead_span),
            lead_length=fd(config.lead_length),
            lead_contact_length=fd(config.lead_contact_length),
            lead_width=fd(config.lead_width),
        )
        full_description = (
            description + '\n\nPitch: {pitch:.3f} mm\n'
            'Body size: {body_size_x:.2f} x {body_size_y:.2f} x {body_size_z:.2f} mm\n'
            'Tab size (max): {tab_size_x:.2f} x {tab_size_y:.2f} mm\n'
            'Lead length: {lead_length:.2f} mm\n'
            'Lead span: {lead_span:.2f} mm\n'
            'Lead width: {lead_width:.2f} mm'
        )
        full_description = full_description.format(
            variation=config.variation,
            pin_count=config.pin_count,
            pitch=config.pitch,
            body_size_x=config.body_size_x,
            body_size_y=config.body_size_y,
            body_size_z=config.body_size_z,
            tab_size_x=config.tab_size_x,
            tab_size_y=config.tab_size_y,
            lead_span=config.lead_span,
            lead_length=config.lead_length,
            lead_width=config.lead_width,
        ) + '\n\nGenerated with {}'.format(generator)

        def _uuid(identifier: str) -> str:
            return uuid(category, full_name, identifier)

        uuid_pkg = _uuid('pkg')
        uuid_pads = [_uuid('pad-{}'.format(p)) for p in range(1, config.pin_count + 1)]

        print('Generating {}: {}'.format(full_name, uuid_pkg))

        package = Package(
            uuid=uuid_pkg,
            name=Name(full_name),
            description=Description(full_description),
            keywords=Keywords(keywords),
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

        for p in range(1, config.pin_count + 1):
            package.add_pad(PackagePad(uuid_pads[p - 1], Name(str(p))))

        def add_footprint_variant(
            key: str,
            name: str,
            density_level: str,
        ) -> None:
            footprint = Footprint(
                uuid=_uuid('{}-footprint'.format(key)),
                name=Name(name),
                description=Description(''),
                position_3d=Position3D.zero(),
                rotation_3d=Rotation3D.zero(),
            )
            footprint.add_tag('ipc-density-level-{}'.format(density_level.lower()))
            package.add_footprint(footprint)

            # Pad excess according to IPC density levels
            excess = excess_by_density(config.pitch, density_level)
            tab_excess = TAB_DENSITY_LEVELS[density_level]

            # Pads
            pad_width = config.lead_width + 2 * excess.side
            pad_length = config.lead_contact_length + excess.heel + excess.toe
            thermal_width = max(config.tab_size_y + 2 * tab_excess.side, config.min_thermal_size_y)
            thermal_length = config.tab_size_x + tab_excess.heel + tab_excess.toe
            thermal_center_x = max_x - thermal_length / 2 + tab_excess.toe
            min_copper_x = 0.0
            max_copper_x = 0.0
            for pin in range(1, config.pin_count + 1):
                pad_uuid = uuid_pads[pin - 1]
                if pin == config.tab_pin_number:
                    width = thermal_width
                    length = thermal_length
                    x = thermal_center_x
                    y = 0.0
                    radius = 0.0
                    function = PadFunction.THERMAL_PAD
                    solder_paste = SolderPasteConfig.OFF
                else:
                    width = pad_width
                    length = pad_length
                    x = min_x + pad_length / 2 - excess.toe
                    y = config.pin1_y - (pin - 1) * config.pitch
                    radius = 0.5
                    function = PadFunction.STANDARD_PAD
                    solder_paste = SolderPasteConfig.AUTO

                footprint.add_pad(
                    FootprintPad(
                        uuid=pad_uuid,
                        side=ComponentSide.TOP,
                        shape=Shape.ROUNDED_RECT,
                        position=Position(x, y),
                        rotation=Rotation(0),
                        size=Size(length, width),
                        radius=ShapeRadius(radius),
                        stop_mask=StopMaskConfig(StopMaskConfig.AUTO),
                        solder_paste=solder_paste,
                        copper_clearance=CopperClearance(0.0),
                        function=function,
                        package_pad=PackagePadUuid(pad_uuid),
                        holes=[],
                    )
                )
                min_copper_x = min(min_copper_x, x - length / 2)
                max_copper_x = max(max_copper_x, x + length / 2)

            # Thermal solder paste according specified coverage
            thermal_area = thermal_width * thermal_length
            thermal_aspect_ratio = thermal_width / thermal_length
            solder_paste_fields = (
                config.thermal_solder_paste_rows * config.thermal_solder_paste_rows
            )
            solder_paste_area = (
                thermal_area * config.thermal_solder_paste_coverage
            ) / solder_paste_fields
            solder_paste_length = math.sqrt(solder_paste_area / thermal_aspect_ratio)
            solder_paste_width = solder_paste_area / solder_paste_length
            dx = solder_paste_length / 2
            dy = solder_paste_width / 2
            solder_paste_pitch_x = 0.98 * thermal_length / config.thermal_solder_paste_rows
            solder_paste_pitch_y = 0.98 * thermal_width / config.thermal_solder_paste_rows
            solder_paste_x0 = (
                thermal_center_x
                - (solder_paste_pitch_x * (config.thermal_solder_paste_rows - 1)) / 2
            )
            solder_paste_y0 = (solder_paste_pitch_y * (config.thermal_solder_paste_rows - 1)) / 2
            for i in range(solder_paste_fields):
                x = solder_paste_x0 + solder_paste_pitch_x * (i % config.thermal_solder_paste_rows)
                y = solder_paste_y0 - solder_paste_pitch_y * (i // config.thermal_solder_paste_rows)
                footprint.add_polygon(
                    Polygon(
                        uuid=_uuid('{}-solder-paste-{}'.format(key, i + 1)),
                        layer=Layer('top_solder_paste'),
                        width=Width(0),
                        fill=Fill(True),
                        grab_area=GrabArea(False),
                        vertices=[
                            Vertex(Position(x - dx, y + dy), Angle(0)),
                            Vertex(Position(x + dx, y + dy), Angle(0)),
                            Vertex(Position(x + dx, y - dy), Angle(0)),
                            Vertex(Position(x - dx, y - dy), Angle(0)),
                            Vertex(Position(x - dx, y + dy), Angle(0)),
                        ],
                    )
                )

            # Documentation body
            dx = config.body_size_x / 2 - LINE_WIDTH / 2
            dy = config.body_size_y / 2 - LINE_WIDTH / 2
            dy_tab = config.tab_size_y / 2
            footprint.add_polygon(
                Polygon(
                    uuid=_uuid('{}-documentation-body'.format(key)),
                    layer=Layer('top_documentation'),
                    width=Width(LINE_WIDTH),
                    fill=Fill(False),
                    grab_area=GrabArea(False),
                    vertices=[
                        Vertex(Position(dx, dy_tab), Angle(0)),
                        Vertex(Position(dx, dy), Angle(0)),
                        Vertex(Position(-dx, dy), Angle(0)),
                        Vertex(Position(-dx, -dy), Angle(0)),
                        Vertex(Position(dx, -dy), Angle(0)),
                        Vertex(Position(dx, -dy_tab), Angle(0)),
                    ],
                )
            )

            # Documentation tab
            x1 = config.body_size_x / 2 + config.tab_overhang
            x0 = x1 - config.tab_size_x
            dy = config.tab_size_y / 2
            footprint.add_polygon(
                Polygon(
                    uuid=_uuid(
                        '{}-documentation-lead-contact-{}'.format(key, config.tab_pin_number)
                    ),
                    layer=Layer('top_documentation'),
                    width=Width(0),
                    fill=Fill(True),
                    grab_area=GrabArea(False),
                    vertices=[
                        Vertex(Position(x0, dy), Angle(0)),
                        Vertex(Position(max_x, dy), Angle(0)),
                        Vertex(Position(max_x, -dy), Angle(0)),
                        Vertex(Position(x0, -dy), Angle(0)),
                        Vertex(Position(x0, dy), Angle(0)),
                    ],
                )
            )

            # Documentation leads
            x1 = min_x + config.lead_contact_length
            x2 = -config.body_size_x / 2
            dy = config.lead_width / 2
            for pin in [
                pin for pin in range(1, config.pin_count + 1) if pin != config.tab_pin_number
            ]:
                y = config.pin1_y - (pin - 1) * config.pitch
                footprint.add_polygon(
                    Polygon(
                        uuid=_uuid('{}-documentation-lead-contact-{}'.format(key, pin)),
                        layer=Layer('top_documentation'),
                        width=Width(0),
                        fill=Fill(True),
                        grab_area=GrabArea(False),
                        vertices=[
                            Vertex(Position(min_x, y + dy), Angle(0)),
                            Vertex(Position(x1, y + dy), Angle(0)),
                            Vertex(Position(x1, y - dy), Angle(0)),
                            Vertex(Position(min_x, y - dy), Angle(0)),
                            Vertex(Position(min_x, y + dy), Angle(0)),
                        ],
                    )
                )
                footprint.add_polygon(
                    Polygon(
                        uuid=_uuid('{}-documentation-lead-projection-{}'.format(key, pin)),
                        layer=Layer('top_documentation'),
                        width=Width(0),
                        fill=Fill(True),
                        grab_area=GrabArea(False),
                        vertices=[
                            Vertex(Position(x1, y + dy), Angle(0)),
                            Vertex(Position(x2, y + dy), Angle(0)),
                            Vertex(Position(x2, y - dy), Angle(0)),
                            Vertex(Position(x1, y - dy), Angle(0)),
                            Vertex(Position(x1, y + dy), Angle(0)),
                        ],
                    )
                )

            # Legend
            dx = config.body_size_x / 2 + LINE_WIDTH / 2
            dy_body = config.body_size_y / 2 + LINE_WIDTH / 2
            dy_tab = round(thermal_width / 2 + LINE_WIDTH / 2 + LEGEND_OFFSET + 0.005, 2)
            footprint.add_polygon(
                Polygon(
                    uuid=_uuid('{}-legend'.format(key)),
                    layer=Layer('top_legend'),
                    width=Width(LINE_WIDTH),
                    fill=Fill(False),
                    grab_area=GrabArea(False),
                    vertices=[
                        Vertex(Position(dx, dy_tab), Angle(0)),
                        Vertex(Position(dx, dy_body), Angle(0)),
                        Vertex(Position(-dx, dy_body), Angle(0)),
                        Vertex(Position(-dx, -dy_body), Angle(0)),
                        Vertex(Position(dx, -dy_body), Angle(0)),
                        Vertex(Position(dx, -dy_tab), Angle(0)),
                    ],
                )
            )

            def _create_outline(
                offset: float = 0, pads_offset: Optional[float] = None
            ) -> list[Vertex]:
                x0 = min_x - offset
                x1 = -config.body_size_x / 2 - offset
                x2 = config.body_size_x / 2 + offset
                x3 = max_x + offset
                leads_dy = config.pin1_y + config.lead_width / 2 + offset
                body_dy = config.body_size_y / 2 + offset
                tab_dy = config.tab_size_y / 2 + offset
                if pads_offset is not None:
                    x0 = min(x0, min_copper_x - pads_offset)
                    x3 = max(x3, max_copper_x + pads_offset)
                    leads_dy = max(leads_dy, config.pin1_y + pad_width / 2 + pads_offset)
                    tab_dy = max(tab_dy, thermal_width / 2 + pads_offset)
                return [
                    Vertex(Position(x1, body_dy), Angle(0)),  # NW
                    Vertex(Position(x2, body_dy), Angle(0)),  # NE
                    Vertex(Position(x2, tab_dy), Angle(0)),
                    Vertex(Position(x3, tab_dy), Angle(0)),
                    Vertex(Position(x3, -tab_dy), Angle(0)),
                    Vertex(Position(x2, -tab_dy), Angle(0)),
                    Vertex(Position(x2, -body_dy), Angle(0)),  # SE
                    Vertex(Position(x1, -body_dy), Angle(0)),  # SW
                    Vertex(Position(x1, -tab_dy), Angle(0)),
                    Vertex(Position(x0, -tab_dy), Angle(0)),
                    Vertex(Position(x0, leads_dy), Angle(0)),
                    Vertex(Position(x1, leads_dy), Angle(0)),
                ]

            # Package Outline
            footprint.add_polygon(
                Polygon(
                    uuid=_uuid('{}-outline'.format(key)),
                    layer=Layer('top_package_outlines'),
                    width=Width(0),
                    fill=Fill(False),
                    grab_area=GrabArea(False),
                    vertices=_create_outline(),
                )
            )

            # Courtyard
            footprint.add_polygon(
                Polygon(
                    uuid=_uuid('{}-courtyard'.format(key)),
                    layer=Layer('top_courtyard'),
                    width=Width(0),
                    fill=Fill(False),
                    grab_area=GrabArea(False),
                    vertices=_create_outline(excess.courtyard, COURTYARD_AROUND_PADS),
                )
            )

            # Labels
            y_max = config.body_size_y / 2 + LINE_WIDTH + 0.5
            y_min = -y_max
            footprint.add_text(
                StrokeText(
                    uuid=_uuid('{}-name'.format(key)),
                    layer=Layer('top_names'),
                    height=Height(TEXT_HEIGHT),
                    stroke_width=StrokeWidth(0.2),
                    letter_spacing=LetterSpacing.AUTO,
                    line_spacing=LineSpacing.AUTO,
                    align=Align('center bottom'),
                    position=Position(0.0, y_max),
                    rotation=Rotation(0.0),
                    auto_rotate=AutoRotate(True),
                    mirror=Mirror(False),
                    value=Value('{{NAME}}'),
                )
            )
            footprint.add_text(
                StrokeText(
                    uuid=_uuid('{}-value'.format(key)),
                    layer=Layer('top_values'),
                    height=Height(TEXT_HEIGHT),
                    stroke_width=StrokeWidth(0.2),
                    letter_spacing=LetterSpacing.AUTO,
                    line_spacing=LineSpacing.AUTO,
                    align=Align('center top'),
                    position=Position(0.0, y_min),
                    rotation=Rotation(0.0),
                    auto_rotate=AutoRotate(True),
                    mirror=Mirror(False),
                    value=Value('{{VALUE}}'),
                )
            )

            # Approvals
            package.add_approval(
                '(approved smt_pad_without_solder_paste\n'
                f' (footprint {footprint.uuid})\n'
                f' (pad {uuid_pads[config.tab_pin_number - 1]})\n'
                ')'
            )

        add_footprint_variant('density~b', 'Density Level B (median protrusion)', 'B')
        add_footprint_variant('density~a', 'Density Level A (max protrusion)', 'A')
        add_footprint_variant('density~c', 'Density Level C (min protrusion)', 'C')

        # Generate 3D models
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

    body_standoff = 0.03
    body_height = config.body_size_z - body_standoff
    body_chamfer = 0.2
    leg_height = 0.5
    leg_z_top = body_standoff + (body_height / 2) + (leg_height / 2)
    stub_leg_length = 0.6
    bend_radius = 0.1 + (leg_height / 2)
    bend_angle = 60

    body = (
        cq.Workplane('XY', origin=(0, 0, body_standoff + (body_height / 2)))
        .box(config.body_size_x, config.body_size_y, body_height)
        .edges()
        .chamfer(body_chamfer)
    )
    bend_angle_rad = math.radians(bend_angle)
    leg_arc_dz = 2 * bend_radius * (1 - math.cos(bend_angle_rad))
    leg_dy = (leg_z_top - leg_height - leg_arc_dz) / math.sin(bend_angle_rad)
    leg_path = (
        cq.Workplane('XZ')
        .hLine(config.lead_contact_length - (leg_height / 2) - bend_radius)
        .ellipseArc(
            x_radius=bend_radius, y_radius=bend_radius, angle1=270, angle2=270 + bend_angle, sense=1
        )
        .line(leg_dy * math.cos(bend_angle_rad), leg_dy * math.sin(bend_angle_rad))
        .ellipseArc(
            x_radius=bend_radius, y_radius=bend_radius, angle1=90, angle2=90 + bend_angle, sense=-1
        )
        .hLine(config.lead_span / 2)
    )
    leg = cq.Workplane('ZY').rect(leg_height, config.lead_width).sweep(leg_path)
    tab = cq.Workplane(
        'XY', origin=(config.body_size_x / 2 + config.tab_overhang - config.tab_size_x, 0, 0)
    ).box(config.tab_size_x, config.tab_size_y, config.tab_size_z, centered=(False, True, False))

    assembly = StepAssembly(full_name)
    assembly.add_body(body, 'body', StepColor.IC_BODY)
    assembly.add_body(tab, 'tab', StepColor.LEAD_SMT)
    for i in range(1, config.pin_count + 1):
        x = config.body_size_x / 2 + config.tab_overhang - config.lead_span
        if i == config.tab_pin_number:
            bbox = cast(cq.Shape, leg.val()).BoundingBox()
            x += bbox.xlen + config.lead_length - stub_leg_length
        rot = 180.0 if i == config.tab_pin_number else 0.0
        assembly.add_body(
            leg,
            'leg-{}'.format(i),
            StepColor.LEAD_SMT,
            location=cq.Location(
                (
                    x,
                    config.pin1_y - (i - 1) * config.pitch,
                    leg_height / 2,
                ),
                (0, 0, rot),
            ),
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

    # TO-252F
    # https://www.jedec.org/system/files/docs/TO-252F.pdf
    # Note: Only added the variants which really exist in real world.
    configs = [
        Config(
            variation='AA',
            pin_count=3,  # including thermal tab
            pitch=2.286,  # 'e'
            body_size_x=6.10,  # 'D'
            body_size_y=6.54,  # 'E' (6.350..6.731)
            body_size_z=2.388,  # 'A' (max value)
            # Note: JEDEC specifies only a minimum value for 'D1', no nominal or
            # maximum. This is stupid, as we need to know its maximum value for
            # determining the pad size (verified with Footprint Expert).
            # Therefore we use a value used in manufacturer datasheets.
            tab_size_x=5.60,  # 'D1'
            tab_size_y=5.461,  # 'b3' (using max. value according Footptint Expert)
            tab_size_z=0.67,  # 'c2' (0.457..0.889)
            tab_overhang=1.08,  # 'L3' (0.889..1.270)
            lead_span=9.91,  # 'H' (9.398..10.414)
            lead_contact_length=1.524,  # 'L'
            lead_width=0.77,  # 'b' (0.635..0.889)
            min_thermal_size_y=5.5,  # Best guess, due to large tolerance of 'b3'
            thermal_solder_paste_rows=3,  # from Footprint Expert
            thermal_solder_paste_coverage=0.6,  # from Footprint Expert
            alternative_names=[AlternativeName('TO-252AA', 'JEDEC')],
        ),
    ]
    generate_pkg(
        library='LibrePCB_Base.lplib',
        author='U. Bruhin',
        name='DPAK{pin_count}P{pitch}_{lead_span}X{body_size_z}L{lead_contact_length}X{lead_width}T{tab_size_x}X{tab_size_y}',
        description='{pin_count}-pin DPAK, standardized by JEDEC TO-252F, variation {variation}.',
        configs=configs,
        generate_3d_models=generate_3d_models,
        pkgcat='a1c24335-5cdc-4eea-9319-2b01132e3af8',  # DPAK
        keywords='jedec,to-252f,to252f',
        version='0.1',
        create_date='2026-06-01T08:27:05Z',
    )
    save_cache(uuid_cache_file, uuid_cache)
