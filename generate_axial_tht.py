"""
Generate axial THT packages like diodes or capacitors.

- JEDEC DO-204 https://www.jedec.org/system/files/docs/DO-204B-D.PDF

"""
import sys
from math import acos, asin, pi, sqrt
from os import path
from uuid import uuid4

from typing import Iterable, List, Optional, Tuple

from common import init_cache, now, save_cache
from entities.common import (
    Align, Angle, Author, Category, Circle, Created, Deprecated, Description, Diameter, Fill, GeneratedBy, GrabArea,
    Height, Keywords, Layer, Name, Polygon, Position, Position3D, Rotation, Rotation3D, Value, Version, Vertex, Width
)
from entities.package import (
    AssemblyType, AutoRotate, ComponentSide, CopperClearance, DrillDiameter, Footprint, Footprint3DModel, FootprintPad,
    LetterSpacing, LineSpacing, Mirror, Package, Package3DModel, PackagePad, PackagePadUuid, PadFunction, PadHole,
    Shape, ShapeRadius, Size, SolderPasteConfig, StopMaskConfig, StrokeText, StrokeWidth
)

generator = 'librepcb-parts-generator (generate_axial_tht.py)'

line_width = 0.2
courtyard_excess = 0.4


# Initialize UUID cache
uuid_cache_file = 'uuid_cache_axial_tht.csv'
uuid_cache = init_cache(uuid_cache_file)


def uuid(category: str, full_name: str, identifier: str) -> str:
    key = '{}-{}-{}'.format(category, full_name, identifier).lower().replace(' ', '~')
    if key not in uuid_cache:
        uuid_cache[key] = str(uuid4())
    return uuid_cache[key]


def calculate_pad_hole_diameter(max_leg_diameter: float) -> float:
    """
    Calculate the typical pad hole diameter for a given maximum leg diameter.

    Currently this is the leg diameter plus 0.05mm, and the result is rounded
    up to the next 0.1mm. But there is no practical proof yet that this works
    fine so in case of issues, it might need to be reworked.
    """
    return round(max_leg_diameter + 0.1, 1)


def calculate_pad_size(hole_diameter: float, compact: bool) -> Tuple[float, float]:
    """
    Calculate the typical pad size for a given pad hole diameter, either
    for a normal or a compact pad.

    Note that there is no practical proof yet that this works fine so in
    case of issues, it might need to be reworked.
    """
    restring = min(0.35 * hole_diameter, 0.5)
    width = hole_diameter + 2 * restring
    length = width if compact else 1.5 * width
    return (length, width)


class FootprintVariant:
    def __init__(
        self,
        vertical: bool,
        pitch: float,
        compact: bool,
        pad_size: Optional[Tuple[float, float]] = None,
    ):
        self.vertical = vertical
        self.pitch = pitch
        self.compact = compact
        self.pad_size = pad_size


def generate_pkg(
    library: str,
    pkg_type: str,
    pkg_identifier: str,
    name: str,
    description: str,
    keywords: str,
    leg_diameter_nom: float,
    body_diameter_nom: float,
    body_length_nom: float,
    pad_names: Tuple[str, str],
    pad_hole_diameter: float,
    variants: Iterable[FootprintVariant],
    author: str,
    pkgcat: str,
    version: str,
    create_date: Optional[str],
    generate_3d_models: bool,
) -> None:
    full_desc = description + f"""

Body diameter: {body_diameter_nom:.2f} mm
Body length: {body_length_nom:.2f} mm
Legs diameter: {leg_diameter_nom:.2f} mm

Generated with {generator}
"""

    def _uuid(identifier: str) -> str:
        return uuid('pkg', pkg_identifier, identifier)

    uuid_pkg = _uuid('pkg')

    print('Generating {}: {}'.format(name, uuid_pkg))

    package = Package(
        uuid=uuid_pkg,
        name=Name(name),
        description=Description(full_desc),
        keywords=Keywords(keywords),
        author=Author(author),
        version=Version(version),
        created=Created(create_date or now()),
        deprecated=Deprecated(False),
        generated_by=GeneratedBy(''),
        categories=[Category(pkgcat)],
        assembly_type=AssemblyType.THT,
    )

    for i, name in enumerate(pad_names):
        package.add_pad(PackagePad(uuid=_uuid('pad-' + str(i + 1)), name=Name(name)))

    generated_3d_uuids = set()
    for variant in variants:
        uuid_ns = '{}{}-'.format('v' if variant.vertical else 'h', variant.pitch)
        footprint_name = '{}, {}mm'.format('Vertical' if variant.vertical else 'Horizontal', variant.pitch)

        if variant.compact:
            uuid_ns += 'compact-'
            footprint_name += ', Compact'
        footprint = Footprint(
            uuid=_uuid(uuid_ns + 'footprint'),
            name=Name(footprint_name),
            description=Description(''),
            position_3d=Position3D.zero(),
            rotation_3d=Rotation3D.zero(),
        )
        package.add_footprint(footprint)

        # Pads
        pad_size = variant.pad_size or calculate_pad_size(pad_hole_diameter, variant.compact)
        if variant.vertical:
            pad_size = (pad_size[1], pad_size[0])
        for i, sign in enumerate([-1, 1]):
            uuid_pad = _uuid(uuid_ns + 'pad-{}'.format(i + 1))
            footprint.add_pad(FootprintPad(
                uuid=uuid_pad,
                side=ComponentSide.TOP,
                shape=Shape.ROUNDED_RECT,
                position=Position(sign * variant.pitch / 2, 0),
                rotation=Rotation(0),
                size=Size(*pad_size),
                radius=ShapeRadius(0 if (i == 0) else 1),
                stop_mask=StopMaskConfig.AUTO,
                solder_paste=SolderPasteConfig.OFF,
                copper_clearance=CopperClearance(0),
                function=PadFunction.STANDARD_PAD,
                package_pad=PackagePadUuid(uuid_pad),
                holes=[PadHole(uuid_pad, DrillDiameter(pad_hole_diameter),
                               [Vertex(Position(0.0, 0.0), Angle(0.0))])],
            ))

        # Documentation
        if variant.vertical:
            footprint.add_circle(Circle(
                uuid=_uuid(uuid_ns + 'circle-body'),
                layer=Layer('top_documentation'),
                width=Width(line_width),
                fill=Fill(False),
                grab_area=GrabArea(True),
                diameter=Diameter(body_diameter_nom - line_width),
                position=Position(-variant.pitch / 2, 0),
            ))
            dx = (variant.pitch / 2)
            footprint.add_polygon(Polygon(
                uuid=_uuid(uuid_ns + 'polygon-leg'),
                layer=Layer('top_documentation'),
                width=Width(leg_diameter_nom),
                fill=Fill(False),
                grab_area=GrabArea(False),
                vertices=[
                    Vertex(Position(-dx, 0), Angle(0)),
                    Vertex(Position(dx, 0), Angle(0)),
                ],
            ))
        else:
            dx = (body_length_nom / 2) - (line_width / 2)
            dy = (body_diameter_nom / 2) - (line_width / 2)
            footprint.add_polygon(Polygon(
                uuid=_uuid(uuid_ns + 'polygon-body'),
                layer=Layer('top_documentation'),
                width=Width(line_width),
                fill=Fill(False),
                grab_area=GrabArea(True),
                vertices=[
                    Vertex(Position(-dx, dy), Angle(0)),  # NW
                    Vertex(Position(dx, dy), Angle(0)),  # NE
                    Vertex(Position(dx, -dy), Angle(0)),  # SE
                    Vertex(Position(-dx, -dy), Angle(0)),  # SW
                    Vertex(Position(-dx, dy), Angle(0)),  # NW
                ],
            ))
            for i, sign in enumerate([-1, 1]):
                x0 = sign * (variant.pitch / 2)
                x1 = sign * (body_length_nom / 2)
                dy = leg_diameter_nom / 2
                footprint.add_polygon(Polygon(
                    uuid=_uuid(uuid_ns + 'polygon-leg{}'.format(i + 1)),
                    layer=Layer('top_documentation'),
                    width=Width(0),
                    fill=Fill(True),
                    grab_area=GrabArea(True),
                    vertices=[
                        Vertex(Position(x0, dy), Angle(0)),
                        Vertex(Position(x1, dy), Angle(0)),
                        Vertex(Position(x1, -dy), Angle(0)),
                        Vertex(Position(x0, -dy), Angle(sign * 180)),
                        Vertex(Position(x0, dy), Angle(0)),
                    ],
                ))

        # Silkscreen
        if variant.vertical:
            silk_pad_clearance_left = (body_diameter_nom / 2) - \
                sqrt(pad_size[0] ** 2 + pad_size[1] ** 2) / 2
            silk_pad_clearance_right = \
                variant.pitch - (body_diameter_nom / 2) - (pad_size[0] / 2) - line_width
            silk_pad_clearance = min(silk_pad_clearance_left, silk_pad_clearance_right)
            simple_silkscreen = silk_pad_clearance < 0.15
            if not simple_silkscreen:
                footprint.add_circle(Circle(
                    uuid=_uuid(uuid_ns + 'circle-legend'),
                    layer=Layer('top_legend'),
                    width=Width(line_width),
                    fill=Fill(False),
                    grab_area=GrabArea(True),
                    diameter=Diameter(body_diameter_nom + line_width),
                    position=Position(-variant.pitch / 2, 0),
                ))
            x0 = (-variant.pitch / 2) + (body_diameter_nom / 2) + (line_width / 2)
            x1 = (variant.pitch / 2) - (pad_size[0] / 2) - 0.15
            dy = leg_diameter_nom / 2
            if x1 - x0 >= 0.1:
                footprint.add_polygon(Polygon(
                    uuid=_uuid(uuid_ns + 'polygon-legend-leg'),
                    layer=Layer('top_legend'),
                    width=Width(0),
                    fill=Fill(True),
                    grab_area=GrabArea(False),
                    vertices=[
                        Vertex(Position(x0, dy), Angle(0)),
                        Vertex(Position(x1, dy), Angle(0)),
                        Vertex(Position(x1, -dy), Angle(0)),
                        Vertex(Position(x0, -dy), Angle(0)),
                        Vertex(Position(x0, dy), Angle(0)),
                    ],
                ))
        else:
            silk_pad_clearance = (variant.pitch - pad_size[0] - body_length_nom) / 2
            if silk_pad_clearance < 0.25:  # 0.1mm line plus 0.15mm clearance
                split_silkscreen = True
                silkscreen_width = line_width
            else:
                split_silkscreen = False
                silkscreen_width = line_width if (silk_pad_clearance - line_width >= 0.15) else 0.1
            dx = (body_length_nom / 2) + (silkscreen_width / 2)
            dy = (body_diameter_nom / 2) + (silkscreen_width / 2)
            if split_silkscreen:
                footprint.add_polygon(Polygon(
                    uuid=_uuid(uuid_ns + 'polygon-legend-top'),
                    layer=Layer('top_legend'),
                    width=Width(silkscreen_width),
                    fill=Fill(False),
                    grab_area=GrabArea(False),
                    vertices=[
                        Vertex(Position(-dx, dy), Angle(0)),
                        Vertex(Position(dx, dy), Angle(0)),
                    ],
                ))
                footprint.add_polygon(Polygon(
                    uuid=_uuid(uuid_ns + 'polygon-legend-bottom'),
                    layer=Layer('top_legend'),
                    width=Width(silkscreen_width),
                    fill=Fill(False),
                    grab_area=GrabArea(False),
                    vertices=[
                        Vertex(Position(-dx, -dy), Angle(0)),
                        Vertex(Position(dx, -dy), Angle(0)),
                    ],
                ))
            else:
                footprint.add_polygon(Polygon(
                    uuid=_uuid(uuid_ns + 'polygon-legend-body'),
                    layer=Layer('top_legend'),
                    width=Width(silkscreen_width),
                    fill=Fill(False),
                    grab_area=GrabArea(False),
                    vertices=[
                        Vertex(Position(-dx, dy), Angle(0)),  # NW
                        Vertex(Position(dx, dy), Angle(0)),  # NE
                        Vertex(Position(dx, -dy), Angle(0)),  # SE
                        Vertex(Position(-dx, -dy), Angle(0)),  # SW
                        Vertex(Position(-dx, dy), Angle(0)),  # NW
                    ],
                ))
            for i, sign in enumerate([-1, 1]):
                x0 = sign * ((variant.pitch / 2) - (pad_size[0] / 2) - 0.2)
                x1 = sign * ((body_length_nom / 2) + silkscreen_width)
                if abs(x0) - abs(x1) < 0.1:
                    continue  # No space left for this polygon
                dy = leg_diameter_nom / 2
                footprint.add_polygon(Polygon(
                    uuid=_uuid(uuid_ns + 'polygon-legend-leg{}'.format(i + 1)),
                    layer=Layer('top_legend'),
                    width=Width(0),
                    fill=Fill(True),
                    grab_area=GrabArea(False),
                    vertices=[
                        Vertex(Position(x0, dy), Angle(0)),
                        Vertex(Position(x1, dy), Angle(0)),
                        Vertex(Position(x1, -dy), Angle(0)),
                        Vertex(Position(x0, -dy), Angle(0)),
                        Vertex(Position(x0, dy), Angle(0)),
                    ],
                ))

        # Pin-1 markings
        bar_width = min(0.2 * body_length_nom, 0.8)
        bar_position = 0.2
        if variant.vertical:
            r = (body_diameter_nom / 2) + (line_width if simple_silkscreen else 0.01)
            h = r - ((pad_size[0] / 2) + 0.15)
            x = -(variant.pitch / 2) - r + h
            dy = sqrt(2 * r * h - h ** 2)
            angle = 360 * acos(1 - (h / r)) / pi
            footprint.add_polygon(Polygon(
                uuid=_uuid(uuid_ns + 'polygon-legend-bar'),
                layer=Layer('top_legend'),
                width=Width(0),
                fill=Fill(True),
                grab_area=GrabArea(False),
                vertices=[
                    Vertex(Position(x, dy), Angle(0)),
                    Vertex(Position(x, -dy), Angle(-angle)),
                    Vertex(Position(x, dy), Angle(0)),
                ],
            ))
        else:
            x = (-body_length_nom / 2) + bar_position * body_length_nom
            x1 = x - (bar_width / 2)
            x2 = x + (bar_width / 2)
            dy = (body_diameter_nom / 2) - line_width
            footprint.add_polygon(Polygon(
                uuid=_uuid(uuid_ns + 'polygon-bar'),
                layer=Layer('top_documentation'),
                width=Width(0),
                fill=Fill(True),
                grab_area=GrabArea(False),
                vertices=[
                    Vertex(Position(x1, dy), Angle(0)),  # NW
                    Vertex(Position(x2, dy), Angle(0)),  # NE
                    Vertex(Position(x2, -dy), Angle(0)),  # SE
                    Vertex(Position(x1, -dy), Angle(0)),  # SW
                    Vertex(Position(x1, dy), Angle(0)),  # NW
                ],
            ))
            dy = body_diameter_nom / 2
            footprint.add_polygon(Polygon(
                uuid=_uuid(uuid_ns + 'polygon-legend-bar'),
                layer=Layer('top_legend'),
                width=Width(0),
                fill=Fill(True),
                grab_area=GrabArea(False),
                vertices=[
                    Vertex(Position(x1, dy), Angle(0)),  # NW
                    Vertex(Position(x2, dy), Angle(0)),  # NE
                    Vertex(Position(x2, -dy), Angle(0)),  # SE
                    Vertex(Position(x1, -dy), Angle(0)),  # SW
                    Vertex(Position(x1, dy), Angle(0)),  # NW
                ],
            ))

        def _create_outline_vertices(offset: float = 0, around_pads: bool = False) -> List[Vertex]:
            if variant.vertical:
                dy_body = (body_diameter_nom / 2) + offset
                dy_leg = (leg_diameter_nom / 2) + offset
                x0 = -variant.pitch / 2
                h = dy_body - 0.5 * sqrt(4 * dy_body ** 2 - (2 * dy_leg) ** 2)
                x1 = x0 + dy_body - h
                x2 = variant.pitch / 2
                angle = 180 * asin(dy_leg / dy_body) / pi
                return [
                    Vertex(Position(x0, dy_body), Angle(angle - 90)),
                    Vertex(Position(x1, dy_leg), Angle(0)),
                    Vertex(Position(x2, dy_leg), Angle(-180)),
                    Vertex(Position(x2, -dy_leg), Angle(0)),
                    Vertex(Position(x1, -dy_leg), Angle(angle - 90)),
                    Vertex(Position(x0, -dy_body), Angle(-180)),
                ]
            else:
                dx_body = (body_length_nom / 2) + offset
                if around_pads:
                    dx_legs = ((variant.pitch + pad_size[0]) / 2) + offset
                else:
                    dx_legs = ((variant.pitch + leg_diameter_nom) / 2) + offset
                dy_body = (body_diameter_nom / 2) + offset
                if around_pads:
                    dy_legs = (pad_size[1] / 2) + offset
                else:
                    dy_legs = (leg_diameter_nom / 2) + offset
                return [
                    Vertex(Position(-dx_legs, dy_legs), Angle(0)),
                    Vertex(Position(-dx_body, dy_legs), Angle(0)),
                    Vertex(Position(-dx_body, dy_body), Angle(0)),
                    Vertex(Position(dx_body, dy_body), Angle(0)),
                    Vertex(Position(dx_body, dy_legs), Angle(0)),
                    Vertex(Position(dx_legs, dy_legs), Angle(0)),
                    Vertex(Position(dx_legs, -dy_legs), Angle(0)),
                    Vertex(Position(dx_body, -dy_legs), Angle(0)),
                    Vertex(Position(dx_body, -dy_body), Angle(0)),
                    Vertex(Position(-dx_body, -dy_body), Angle(0)),
                    Vertex(Position(-dx_body, -dy_legs), Angle(0)),
                    Vertex(Position(-dx_legs, -dy_legs), Angle(0)),
                ]

        # Package outline
        footprint.add_polygon(Polygon(
            uuid=_uuid(uuid_ns + 'polygon-outline'),
            layer=Layer('top_package_outlines'),
            width=Width(0),
            fill=Fill(False),
            grab_area=GrabArea(False),
            vertices=_create_outline_vertices(),
        ))

        # Courtyard
        footprint.add_polygon(Polygon(
            uuid=_uuid(uuid_ns + 'polygon-courtyard'),
            layer=Layer('top_courtyard'),
            width=Width(0),
            fill=Fill(False),
            grab_area=GrabArea(False),
            vertices=_create_outline_vertices(offset=courtyard_excess, around_pads=True),
        ))

        # Text
        x = (-variant.pitch / 2) if variant.vertical else 0
        footprint.add_text(StrokeText(
            uuid=_uuid(uuid_ns + 'text-name'),
            layer=Layer('top_names'),
            height=Height(1.0),
            stroke_width=StrokeWidth(0.2),
            letter_spacing=LetterSpacing.AUTO,
            line_spacing=LineSpacing.AUTO,
            align=Align('center bottom'),
            position=Position(x, (body_diameter_nom / 2) + line_width + 0.5),
            rotation=Rotation(0.0),
            auto_rotate=AutoRotate(False),
            mirror=Mirror(False),
            value=Value('{{NAME}}'),
        ))
        footprint.add_text(StrokeText(
            uuid=_uuid(uuid_ns + 'text-value'),
            layer=Layer('top_values'),
            height=Height(1.0),
            stroke_width=StrokeWidth(0.2),
            letter_spacing=LetterSpacing.AUTO,
            line_spacing=LineSpacing.AUTO,
            align=Align('center top'),
            position=Position(x, (-body_diameter_nom / 2) - (line_width + 0.5)),
            rotation=Rotation(0.0),
            auto_rotate=AutoRotate(False),
            mirror=Mirror(False),
            value=Value('{{VALUE}}'),
        ))

        # 3D model
        uuid_3d = _uuid('{}{}-3d'.format('v' if variant.vertical else 'h', variant.pitch))
        name_3d = '{}, {} mm'.format('Vertical' if variant.vertical else 'Horizontal', variant.pitch)
        # Note: Some 3D models are used by multiple footprints but they shall
        # be added to the package only once, thus we keep a list of which
        # models were already added.
        if uuid_3d not in generated_3d_uuids:
            if generate_3d_models:
                generate_3d(library, pkg_type, name_3d, uuid_pkg, uuid_3d,
                            body_diameter_nom, body_length_nom, leg_diameter_nom,
                            variant.pitch, variant.vertical, bar_position, bar_width)
            package.add_3d_model(Package3DModel(uuid_3d, Name(name_3d)))
            generated_3d_uuids.add(uuid_3d)
        footprint.add_3d_model(Footprint3DModel(uuid_3d))

    package.serialize(path.join('out', library, 'pkg'))


def generate_3d(
    library: str,
    pkg_type: str,
    name: str,
    uuid_pkg: str,
    uuid_3d: str,
    body_diameter: float,
    body_length: float,
    leg_diameter: float,
    pitch: float,
    vertical: bool,
    marking_position: float,
    marking_width: float,
) -> None:
    import cadquery as cq

    from cadquery_helpers import StepAssembly, StepColor, StepConstants

    print(f'Generating pkg 3D model "{name}": {uuid_3d}')

    vertical_standoff = 0.3
    bend_radius = 0.5
    marking_diameter = body_diameter + 0.05
    marking_offset = body_length * (0.5 - marking_position)

    if vertical:
        body = cq.Workplane("XY") \
            .cylinder(body_length, body_diameter / 2, centered=(True, True, False)) \
            .translate((-pitch / 2, 0, vertical_standoff))
        marking = cq.Workplane("XY") \
            .cylinder(marking_width, marking_diameter / 2, centered=(True, True, False)) \
            .translate((-pitch / 2, 0, vertical_standoff + (body_length / 2) - marking_offset))
    else:
        body = cq.Workplane("YZ") \
            .cylinder(body_length, body_diameter / 2, centered=(True, False, True))
        marking = cq.Workplane("YZ") \
            .cylinder(marking_width, marking_diameter / 2, centered=(True, False, True)) \
            .translate((-marking_offset, 0, 0))

    leg_length = StepConstants.THT_LEAD_SOLDER_LENGTH - bend_radius + \
        ((body_length + 2 * vertical_standoff + (leg_diameter / 2)) if vertical
         else (body_diameter / 2))
    leg_path = cq.Workplane("XZ") \
        .vLine(leg_length) \
        .ellipseArc(x_radius=bend_radius, y_radius=bend_radius, angle1=90, angle2=180, sense=-1) \
        .hLine(pitch - 2 * bend_radius) \
        .ellipseArc(x_radius=bend_radius, y_radius=bend_radius, angle1=0, angle2=90, sense=-1) \
        .vLine(-leg_length)
    leg = cq.Workplane("XY") \
        .circle(leg_diameter / 2) \
        .sweep(leg_path) \
        .translate((-pitch / 2, 0, -StepConstants.THT_LEAD_SOLDER_LENGTH))

    if pkg_type == 'DO':
        body_color = cq.Color('gray16')
    else:
        raise RuntimeError(f'Unsupported 3D package type: {pkg_type}')

    assembly = StepAssembly(name)
    assembly.add_body(body, 'body', body_color)
    assembly.add_body(marking, 'marking', cq.Color('gray80'))
    assembly.add_body(leg, 'leg', StepColor.LEAD_THT)

    out_path = path.join('out', library, 'pkg', uuid_pkg, f'{uuid_3d}.step')
    assembly.save(out_path)


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

    # DO-204 (only the variants which actually exist)
    generate_pkg(
        library='LibrePCB_Base.lplib',
        pkg_type='DO',
        pkg_identifier='do204aa',
        name='DO-204AA',
        description='Diode outline package as specified by JEDEC DO-204AA. ' +
                    'Also known as DO-7.',
        keywords='do204aa,do7,do-7',
        leg_diameter_nom=(0.46 + 0.55) / 2,  # b
        body_diameter_nom=(2.16 + 2.71) / 2,  # D
        body_length_nom=(5.85 + 7.62) / 2,  # G
        pad_names=('1', '2'),
        pad_hole_diameter=calculate_pad_hole_diameter(0.6),  # b max
        variants=[
            FootprintVariant(vertical=False, pitch=10.16, compact=False),
            FootprintVariant(vertical=False, pitch=10.16, compact=True),
            FootprintVariant(vertical=False, pitch=12.7, compact=True),
            FootprintVariant(vertical=False, pitch=15.24, compact=True),
            FootprintVariant(vertical=True, pitch=2.54, compact=True),
            FootprintVariant(vertical=True, pitch=3.81, compact=True),
            FootprintVariant(vertical=True, pitch=5.08, compact=True),
            FootprintVariant(vertical=True, pitch=7.62, compact=True),
        ],
        author='U. Bruhin',
        pkgcat='dcaa6b6c-0c55-43fd-a320-5dd74a2cdc85',
        version='0.1',
        create_date='2023-09-07T13:30:53Z',
        generate_3d_models=generate_3d_models,
    )
    generate_pkg(
        library='LibrePCB_Base.lplib',
        pkg_type='DO',
        pkg_identifier='do204ac',
        name='DO-204AC',
        description='Diode outline package as specified by JEDEC DO-204AC. ' +
                    'Also known as DO-15.',
        keywords='do204ac,do15,do-15',
        leg_diameter_nom=(0.69 + 0.88) / 2,  # b
        body_diameter_nom=(2.65 + 3.55) / 2,  # D
        body_length_nom=(5.85 + 7.62) / 2,  # G
        pad_names=('1', '2'),
        pad_hole_diameter=calculate_pad_hole_diameter(0.88),  # b max
        variants=[
            FootprintVariant(vertical=False, pitch=10.16, compact=False),
            FootprintVariant(vertical=False, pitch=10.16, compact=True),
            FootprintVariant(vertical=False, pitch=12.7, compact=True),
            FootprintVariant(vertical=False, pitch=15.24, compact=True),
            FootprintVariant(vertical=True, pitch=2.54, compact=True),
            FootprintVariant(vertical=True, pitch=3.81, compact=True),
            FootprintVariant(vertical=True, pitch=5.08, compact=True),
            FootprintVariant(vertical=True, pitch=7.62, compact=True),
        ],
        author='U. Bruhin',
        pkgcat='dcaa6b6c-0c55-43fd-a320-5dd74a2cdc85',
        version='0.1',
        create_date='2023-09-07T13:30:53Z',
        generate_3d_models=generate_3d_models,
    )
    generate_pkg(
        library='LibrePCB_Base.lplib',
        pkg_type='DO',
        pkg_identifier='do204ag',
        name='DO-204AG',
        description='Diode outline package as specified by JEDEC DO-204AG. ' +
                    'Also known as DO-34.',
        keywords='do204ag,do43,do-34',
        leg_diameter_nom=(0.46 + 0.55) / 2,  # b
        body_diameter_nom=(1.27 + 1.9) / 2,  # D
        body_length_nom=(2.16 + 3.04) / 2,  # G
        pad_names=('1', '2'),
        pad_hole_diameter=calculate_pad_hole_diameter(0.55),  # b max
        variants=[
            FootprintVariant(vertical=False, pitch=5.08, compact=False),
            FootprintVariant(vertical=False, pitch=5.08, compact=True),
            FootprintVariant(vertical=False, pitch=7.62, compact=True),
            FootprintVariant(vertical=False, pitch=10.16, compact=True),
            FootprintVariant(vertical=False, pitch=12.7, compact=True),
            FootprintVariant(vertical=True, pitch=2.54, compact=True),
            FootprintVariant(vertical=True, pitch=3.81, compact=True),
        ],
        author='U. Bruhin',
        pkgcat='dcaa6b6c-0c55-43fd-a320-5dd74a2cdc85',
        version='0.1',
        create_date='2023-09-07T13:30:53Z',
        generate_3d_models=generate_3d_models,
    )
    generate_pkg(
        library='LibrePCB_Base.lplib',
        pkg_type='DO',
        pkg_identifier='do204ah',
        name='DO-204AH',
        description='Diode outline package as specified by JEDEC DO-204AH. ' +
                    'Also known as DO-35.',
        keywords='do204ah,do35,do-35',
        leg_diameter_nom=(0.46 + 0.55) / 2,  # b
        body_diameter_nom=(1.53 + 2.28) / 2,  # D
        body_length_nom=(3.05 + 5.08) / 2,  # G
        pad_names=('1', '2'),
        pad_hole_diameter=calculate_pad_hole_diameter(0.55),  # b max
        variants=[
            FootprintVariant(vertical=False, pitch=7.62, compact=False),
            FootprintVariant(vertical=False, pitch=7.62, compact=True),
            FootprintVariant(vertical=False, pitch=10.16, compact=True),
            FootprintVariant(vertical=False, pitch=12.7, compact=True),
            FootprintVariant(vertical=True, pitch=2.54, compact=True),
            FootprintVariant(vertical=True, pitch=3.81, compact=True),
            FootprintVariant(vertical=True, pitch=5.08, compact=True),
        ],
        author='U. Bruhin',
        pkgcat='dcaa6b6c-0c55-43fd-a320-5dd74a2cdc85',
        version='0.1',
        create_date='2023-09-07T13:30:53Z',
        generate_3d_models=generate_3d_models,
    )
    generate_pkg(
        library='LibrePCB_Base.lplib',
        pkg_type='DO',
        pkg_identifier='do204al',
        name='DO-204AL',
        description='Diode outline package as specified by JEDEC DO-204AL. ' +
                    'Also known as DO-41.',
        keywords='do204al,do41,do-41',
        leg_diameter_nom=(0.72 + 0.86) / 2,  # b
        body_diameter_nom=(2.04 + 2.71) / 2,  # D
        body_length_nom=(4.07 + 5.2) / 2,  # G
        pad_names=('1', '2'),
        pad_hole_diameter=calculate_pad_hole_diameter(0.86),  # b max
        variants=[
            FootprintVariant(vertical=False, pitch=7.62, compact=False),
            FootprintVariant(vertical=False, pitch=7.62, compact=True),
            FootprintVariant(vertical=False, pitch=10.16, compact=True),
            FootprintVariant(vertical=False, pitch=12.7, compact=True),
            FootprintVariant(vertical=True, pitch=2.54, compact=True),
            FootprintVariant(vertical=True, pitch=3.81, compact=True),
            FootprintVariant(vertical=True, pitch=5.08, compact=True),
        ],
        author='U. Bruhin',
        pkgcat='dcaa6b6c-0c55-43fd-a320-5dd74a2cdc85',
        version='0.1',
        create_date='2023-09-07T13:30:53Z',
        generate_3d_models=generate_3d_models,
    )
    generate_pkg(
        library='LibrePCB_Base.lplib',
        pkg_type='DO',
        pkg_identifier='do204ar',
        name='DO-204AR',
        description='Diode outline package as specified by JEDEC DO-204AR.',
        keywords='do204ar',
        leg_diameter_nom=(1.22 + 1.32) / 2,  # b
        body_diameter_nom=(6.1 + 6.35) / 2,  # D
        body_length_nom=(9.27 + 9.52) / 2,  # G
        pad_names=('1', '2'),
        pad_hole_diameter=calculate_pad_hole_diameter(1.32),  # b max
        variants=[
            FootprintVariant(vertical=False, pitch=15.24, compact=False),
            FootprintVariant(vertical=False, pitch=15.24, compact=True),
            FootprintVariant(vertical=False, pitch=17.78, compact=True),
            FootprintVariant(vertical=False, pitch=20.32, compact=True),
            FootprintVariant(vertical=True, pitch=5.08, compact=True),
            FootprintVariant(vertical=True, pitch=7.62, compact=True),
            FootprintVariant(vertical=True, pitch=10.16, compact=True),
            FootprintVariant(vertical=True, pitch=12.7, compact=True),
        ],
        author='U. Bruhin',
        pkgcat='dcaa6b6c-0c55-43fd-a320-5dd74a2cdc85',
        version='0.1',
        create_date='2023-09-07T13:30:53Z',
        generate_3d_models=generate_3d_models,
    )

    save_cache(uuid_cache_file, uuid_cache)
