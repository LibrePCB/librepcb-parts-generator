"""
Generate DFN packages

"""

import argparse
import logging
from collections import Counter
from math import isclose
from os import path

from typing import Generator, Optional

import qfn_mo_220
import qfn_mo_288B
from common import UuidCache, grid_solderpaste, make_border_rectangle, now
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
    MinCopperClearance,
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
from qfn_common import Variant

generator_name = 'librepcb-parts-generator (generate_qfn.py)'

silkscreen_line_width = 0.254
label_offset = 1.0
body_outline_width = 0.2


def get_y(pin_number: int, pin_count: int, spacing: float) -> float:
    """
    Return the y coordinate of the specified pin.

    The pin number is 1 index based. Pin 1 is at the top. The middle pin will
    be at or near 0.
    """
    mid = (pin_count + 1) / 2
    return -pin_number * spacing + mid * spacing


def center(a: float, b: float) -> float:
    return (a + b) / 2.0


def get_pad_positions(variant: Variant) -> Generator[tuple[str, float], None, None]:
    """
    Calculates side (left, right, top, bottom) and relative position on that side.
    Position is in number-of-pitches, e.g. -1.5, -0.5, +0.5, +1.5.
    Position starts with the first pin on this side, i.e. absolute coordinates must
    sometimes be added, sometimes subtracted.
    """

    def make_side(name: str, pins: int) -> Generator[tuple[str, float], None, None]:
        for i in range(pins):
            yield (name, float(i) - (pins - 1.0) / 2.0)

    yield from make_side('west', variant.num_pins_east_west)
    yield from make_side('south', variant.num_pins_north_south)
    yield from make_side('east', variant.num_pins_east_west)
    yield from make_side('north', variant.num_pins_north_south)


def default_description(variant: Variant) -> str:
    if variant.alternative_names:
        alternative_names = 'Manufacturer-specific names:\n'
        for manufacturer, name in variant.alternative_names:
            alternative_names += f'- {name} ({manufacturer})\n'
    else:
        alternative_names = ''
    return f"""\
{variant.num_pins}-pin Quad Flat No-Lead package (QFN), standardized by {variant.standard}

Pitch: {variant.pitch:.1f} mm
Nominal width: {variant.body_size_y:.2f} mm
Nominal length: {variant.body_size_x:.2f} mm
Height: {variant.overall_height:.2f} mm
{alternative_names}

Generated with {generator_name}
""".strip()


def generate_pkg(
    variant: Variant,
    uuid_cache: UuidCache,
    pkgcat: str,
    generate_3d_models: bool,
    create_date: Optional[str] = None,
    author: str = 'Klaus Neuschwander',
    library: str = 'LibrePCB_Base.lplib',
) -> None:
    category = 'pkg'

    keywords = f'qfn{variant.num_pins}'
    for name, reference in variant.alternative_names:
        keywords += f',{reference.lower()}_{name.lower()}'

    name = variant.name
    if variant.alternative_names:
        name += (
            f' ({",".join(f"{reference}_{name}" for name, reference in variant.alternative_names)})'
        )

    package_uuid = uuid_cache.sub_cache('pkg', variant.name)

    uuid_pkg = package_uuid.get('pkg')
    uuid_pads = [package_uuid.get('pad', p) for p in range(1, variant.num_pins + 1)]
    uuid_exposed_pad = package_uuid.get('exposed')

    logging.info('Generating {variant.name}: {uuid_pkg}')

    # Create package
    package = Package(
        uuid=uuid_pkg,
        name=Name(name),
        description=Description(default_description(variant)),
        keywords=Keywords(keywords),
        author=Author(author),
        version=Version('0.1'),  # TODO: what version is this? package? generator? data format?
        created=Created(create_date or now()),
        deprecated=Deprecated(False),
        generated_by=GeneratedBy(generator_name),
        categories=[Category(pkgcat)],
        assembly_type=AssemblyType.SMT,
        min_copper_clearance=MinCopperClearance(variant.min_clearance),
    )

    for name, reference in variant.alternative_names:
        package.add_alternative_name(AlternativeName(name, reference))

    # Create pads
    for p in range(1, variant.num_pins + 1):
        package.add_pad(PackagePad(uuid_pads[p - 1], Name(str(p))))
    if variant.exposed_pad:
        package.add_pad(PackagePad(uuid_exposed_pad, Name('ExposedPad')))

    # Create Footprint function
    def add_footprint_variant(
        key: str,
        name: str,
        density_level: str,
    ) -> None:
        footprint_uuid = package_uuid.sub_cache('footprint', key)

        # Create Meta-data
        footprint = Footprint(
            uuid=footprint_uuid.get('footprint'),
            name=Name(name),
            description=Description(''),
            position_3d=Position3D.zero(),
            rotation_3d=Rotation3D.zero(),
        )
        footprint.add_tag('ipc-density-level-{}'.format(density_level.lower()))
        package.add_footprint(footprint)

        rel_pad_positions = list(get_pad_positions(variant))

        try:
            heel = 0.0  # adding a heel would break clearance requirements with exposed pad
            toe = dict(
                A=0.30,
                B=0.20,
                C=0.10,
            )[density_level]
            # side: no side excess
            courtyard_excess = dict(
                A=0.40,
                B=0.20,
                C=0.10,
            )[density_level]
        except KeyError:
            raise RuntimeError(f'no default toe/heel defined for pitch {variant.pitch}')

        body_x = variant.body_size_x / 2
        body_y = variant.body_size_y / 2

        stop_mask_config = StopMaskConfig(
            StopMaskConfig.AUTO
            if variant.pitch >= 0.5
            else ((variant.pitch - variant.lead_width) * 0.4)
        )

        # normal pads
        for i_pad in range(variant.num_pins):
            pad_name = i_pad + 1
            side, rel_position = rel_pad_positions[i_pad]

            if side in ('west', 'east'):
                lead_inner = body_x - variant.lead_length_east_west
                pad_inner = lead_inner - heel
                pad_outer = body_x + toe

                pad_width = heel + variant.lead_length_east_west + toe
                center_x = center(pad_inner, pad_outer) * (-1 if side == 'west' else +1)
                center_y = variant.pitch * rel_position * (-1 if side == 'west' else +1)

                lead_x_1 = body_x * (-1 if side == 'west' else +1)
                lead_x_2 = lead_inner * (-1 if side == 'west' else +1)
                lead_y_1 = center_y - variant.lead_width / 2
                lead_y_2 = center_y + variant.lead_width / 2

            else:
                lead_inner = body_y - variant.lead_length_north_south
                pad_inner = lead_inner - heel
                pad_outer = body_y + toe
                pad_width = heel + variant.lead_length_north_south + toe
                center_x = variant.pitch * rel_position * (+1 if side == 'south' else -1)
                center_y = center(pad_inner, pad_outer) * (-1 if side == 'south' else +1)

                lead_x_1 = center_x - variant.lead_width / 2
                lead_x_2 = center_x + variant.lead_width / 2
                lead_y_1 = body_y * (-1 if side == 'south' else +1)
                lead_y_2 = lead_inner * (-1 if side == 'south' else +1)
            assert isclose(pad_outer - pad_inner, pad_width), (pad_outer, pad_inner, pad_width)

            # pad
            footprint.add_pad(
                FootprintPad(
                    uuid=footprint_uuid.get('pad', pad_name),
                    side=ComponentSide.TOP,
                    shape=Shape.ROUNDED_RECT,
                    position=Position(center_x, center_y),
                    rotation=Rotation(0 if side in ('west', 'east') else 90),
                    size=Size(pad_width, variant.lead_width),
                    radius=ShapeRadius(variant.pad_radius),
                    stop_mask=stop_mask_config,
                    solder_paste=SolderPasteConfig.AUTO,
                    copper_clearance=CopperClearance(0.0),
                    function=PadFunction.STANDARD_PAD,
                    package_pad=PackagePadUuid(uuid_pads[i_pad]),
                    holes=[],
                )
            )

            # docu
            footprint.add_polygon(
                Polygon(
                    uuid=footprint_uuid.get('pad', pad_name, 'docu'),
                    layer=Layer('top_documentation'),
                    width=Width(0),
                    fill=Fill(True),
                    grab_area=GrabArea(False),
                    vertices=[
                        Vertex(Position(x, y), Angle(0))
                        for x, y in [
                            (lead_x_1, lead_y_1),
                            (lead_x_1, lead_y_2),
                            (lead_x_2, lead_y_2),
                            (lead_x_2, lead_y_1),
                            (lead_x_1, lead_y_1),
                        ]
                    ],
                )
            )

        # exposed pad
        if variant.exposed_pad:
            footprint.add_pad(
                FootprintPad(
                    uuid=footprint_uuid.get('pad', 'exposed'),
                    side=ComponentSide.TOP,
                    shape=Shape.ROUNDED_RECT,
                    position=Position(0, 0),
                    rotation=Rotation(0),
                    size=Size(variant.exposed_pad.x, variant.exposed_pad.y),
                    radius=ShapeRadius(0),
                    stop_mask=StopMaskConfig(StopMaskConfig.AUTO),
                    solder_paste=SolderPasteConfig.OFF,
                    copper_clearance=CopperClearance(0.0),
                    function=PadFunction.STANDARD_PAD,
                    package_pad=PackagePadUuid(uuid_exposed_pad),
                    holes=[],
                )
            )

            for p in grid_solderpaste(
                uuid_cache=footprint_uuid.sub_cache('exposed_pad_solderpaste'),
                x_min=-variant.exposed_pad.x / 2,
                x_max=+variant.exposed_pad.x / 2,
                y_min=-variant.exposed_pad.y / 2,
                y_max=+variant.exposed_pad.y / 2,
            ):
                footprint.add_polygon(p)
        # package outline
        footprint.add_polygon(
            Polygon(
                uuid=footprint_uuid.get('outline'),
                layer=Layer('top_package_outlines'),
                width=Width(0),
                fill=Fill(False),
                grab_area=GrabArea(False),
                vertices=make_border_rectangle(
                    -body_x, +body_x, +body_y, -body_y, width=0.0, direction='center'
                ),
            )
        )

        # package outline on docu
        footprint.add_polygon(
            Polygon(
                uuid=footprint_uuid.get('outline', 'docu'),
                layer=Layer('top_documentation'),
                width=Width(body_outline_width),
                fill=Fill(False),
                grab_area=GrabArea(False),
                vertices=make_border_rectangle(
                    -body_x, +body_x, +body_y, -body_y, width=body_outline_width, direction='inner'
                ),
            )
        )

        # docu pin1 indicator on package
        footprint.add_circle(
            Circle(
                uuid=footprint_uuid.get('docu', 'pin1indicator'),
                layer=Layer('top_documentation'),
                width=Width(0),
                fill=Fill(True),
                grab_area=GrabArea(False),
                diameter=Diameter(0.2),
                position=Position(
                    -(body_x - 2 * body_outline_width),
                    +(body_y - 2 * body_outline_width),
                ),
            )
        )

        # silkscreen
        silk_x = body_x + silkscreen_line_width / 2
        silk_y = body_y + silkscreen_line_width / 2
        silk_x_end = min(
            silk_x, variant.num_pins_north_south * variant.pitch / 2 + silkscreen_line_width
        )
        silk_y_end = min(
            silk_y, variant.num_pins_east_west * variant.pitch / 2 + silkscreen_line_width
        )

        for x_sign in (-1, 1):
            for y_sign in (-1, 1):
                vertices = [
                    (silk_x_end, silk_y),
                    (silk_x, silk_y),
                    (silk_x, silk_y_end),
                ]

                footprint.add_polygon(
                    Polygon(
                        uuid=footprint_uuid.get('silkscreen', x_sign, y_sign),
                        layer=Layer('top_legend'),
                        width=Width(silkscreen_line_width),
                        fill=Fill(False),
                        grab_area=GrabArea(False),
                        vertices=[
                            Vertex(Position(x * x_sign, y * y_sign), Angle(0)) for x, y in vertices
                        ],
                    )
                )

        # silkscreen pin-1 indicator
        footprint.add_circle(
            Circle(
                uuid=footprint_uuid.get('docu', 'silkscreen', 'pin1indicator'),
                layer=Layer('top_legend'),
                width=Width(0),
                fill=Fill(True),
                grab_area=GrabArea(False),
                diameter=Diameter(silkscreen_line_width),
                position=Position(
                    -(body_x + silkscreen_line_width * 1.5),
                    +(body_y),
                ),
            )
        )

        # courtyard
        footprint.add_polygon(
            generate_courtyard(
                uuid=footprint_uuid.get('courtyard'),
                max_x=body_x + toe,
                max_y=body_y + toe,
                excess_x=courtyard_excess,
                excess_y=courtyard_excess,
            )
        )

        # name
        footprint.add_text(
            StrokeText(
                uuid=footprint_uuid.get('name'),
                layer=Layer('top_names'),
                position=Position(0.0, body_y + label_offset),
                align=Align('center bottom'),
                value=Value('{{NAME}}'),
                height=Height(1),
                stroke_width=StrokeWidth(0.2),
                letter_spacing=LetterSpacing.AUTO,
                line_spacing=LineSpacing.AUTO,
                rotation=Rotation(0),
                auto_rotate=AutoRotate(True),
                mirror=Mirror(False),
            )
        )

        # value
        footprint.add_text(
            StrokeText(
                uuid=footprint_uuid.get('value'),
                layer=Layer('top_values'),
                position=Position(0.0, -(body_y + label_offset)),
                align=Align('center top'),
                value=Value('{{VALUE}}'),
                height=Height(1),
                stroke_width=StrokeWidth(0.2),
                letter_spacing=LetterSpacing.AUTO,
                line_spacing=LineSpacing.AUTO,
                rotation=Rotation(0),
                auto_rotate=AutoRotate(True),
                mirror=Mirror(False),
            )
        )

    # Apply function to available footprints
    add_footprint_variant('density~b', 'Density Level B (median protrusion)', 'B')
    add_footprint_variant('density~a', 'Density Level A (max protrusion)', 'A')
    add_footprint_variant('density~c', 'Density Level C (min protrusion)', 'C')

    # 3d
    if generate_3d_models:
        uuid_3d = package_uuid.get('3d')
        path_3d = path.join('out', library, 'pkg', uuid_pkg, f'{uuid_3d}.step')
        generate_3d(variant, path_3d)
        package.add_3d_model(Package3DModel(uuid_3d, Name(variant.name)))
        for footprint in package.footprints:
            footprint.add_3d_model(Footprint3DModel(uuid_3d))

    # Save package
    package.serialize(path.join('out', library, category))


def generate_3d(variant: Variant, save_path: str) -> None:
    import cadquery as cq

    from cadquery_helpers import StepAssembly, StepColor

    body_chamfer = 0.05
    dot_diameter = 0.3
    dot_depth = 0.15
    dot_offset = 0.5
    dot_center_x = -(variant.body_size_x / 2 - dot_offset)
    dot_center_y = +(variant.body_size_y / 2 - dot_offset)

    body = (
        cq.Workplane('XY', origin=(0, 0, variant.overall_height / 2))
        .box(variant.body_size_x, variant.body_size_y, variant.overall_height)
        .edges()
        .chamfer(body_chamfer)
        .workplane(
            origin=(dot_center_x, dot_center_y), offset=variant.overall_height / 2 - dot_depth
        )
        .cylinder(dot_depth + 0.1, dot_diameter / 2, centered=(True, True, False), combine='cut')
    )
    dot = cq.Workplane('XY', origin=(dot_center_x, dot_center_y)).cylinder(
        variant.overall_height - dot_depth + 0.1, dot_diameter / 2, centered=(True, True, False)
    )
    assembly = StepAssembly(variant.name)
    assembly.add_body(body, 'body', StepColor.IC_BODY)
    assembly.add_body(dot, 'dot', StepColor.IC_PIN1_DOT)
    assembly.save(save_path, fused=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--3d', action='store_true', dest='cadquery', help='Generate 3D models using cadquery'
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    if not args.cadquery:
        logging.warning('Not generating 3D models unless the command line option is selected')

    variants = qfn_mo_220.load_variants() + qfn_mo_288B.load_variants()
    counts = Counter((v.name for v in variants))
    duplicates = [n for n, count in counts.items() if count > 1]
    if duplicates:
        raise RuntimeError(f'Multiple definitions of variants: {duplicates}')

    with UuidCache('uuid_cache_qfn.csv') as uuid_cache:
        for variant in variants:
            print(variant.name)
            try:
                generate_pkg(
                    variant=variant,
                    uuid_cache=uuid_cache,
                    pkgcat='e077449f-2272-41ce-92ce-0cb99dfa0697',
                    generate_3d_models=args.cadquery,
                )
            except Exception as e:
                try:
                    e.add_note(f'While generating variant {variant.name}')  # type: ignore[attr-defined,unused-ignore]
                except AttributeError:
                    pass
                raise
