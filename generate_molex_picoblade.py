"""
Generate packages and devices for the Molex Picoblade family
"""

import sys
from os import path
from uuid import uuid4

from typing import List, Optional

from common import init_cache, now, save_cache
from entities.attribute import Attribute, AttributeType
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
    Resource,
    Rotation,
    Rotation3D,
    Value,
    Version,
    Vertex,
    Width,
)
from entities.component import SignalUUID
from entities.device import (
    ComponentPad,
    ComponentUUID,
    Device,
    Manufacturer,
    PackageUUID,
    Part,
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

generator = 'librepcb-parts-generator (generate_molex_picoblade.py)'

LINE_WIDTH = 0.2
COURTYARD_EXCESS = 0.2


# Initialize UUID cache
uuid_cache_file = 'uuid_cache_molex_picoblade.csv'
uuid_cache = init_cache(uuid_cache_file)

uuid_cache_connectors = init_cache('uuid_cache_connectors.csv')


def uuid(category: str, full_name: str, identifier: str) -> str:
    key = '{}-{}-{}'.format(category, full_name, identifier).lower().replace(' ', '~')
    if key not in uuid_cache:
        uuid_cache[key] = str(uuid4())
    return uuid_cache[key]


def generate_pkg(
    library: str,
    author: str,
    version: str,
    create_date: Optional[str],
    uuid_key: str,
    circuits: int,
    name: str,
    description: str,
    keywords: str,
    categories: List[str],
    generate_3d_models: bool,
) -> None:
    def _uuid(identifier: str) -> str:
        return uuid('pkg', uuid_key, identifier)

    uuid_pkg = _uuid('pkg')

    print(f'Generating {name}: {uuid_pkg}')

    package = Package(
        uuid=uuid_pkg,
        name=Name(name),
        description=Description(description + f'\n\nGenerated with {generator}'),
        keywords=Keywords(keywords),
        author=Author(author),
        version=Version(version),
        created=Created(create_date or now()),
        deprecated=Deprecated(False),
        generated_by=GeneratedBy(''),
        categories=[Category(c) for c in categories],
        assembly_type=AssemblyType.SMT,
    )

    # Footprint
    footprint = Footprint(
        uuid=_uuid('footprint'),
        name=Name('default'),
        description=Description(''),
        position_3d=Position3D.zero(),
        rotation_3d=Rotation3D.zero(),
    )
    package.add_footprint(footprint)

    # The origin is where the package needs to be picked by the vacuum picker,
    # as documented in the datasheet drawing. It is relative to the origin as
    # used in the datasheet drawing, so we can convert the coordinate system.
    origin_x = 1.6  # 0.6mm + (2mm / 2)

    # Pads
    pitch = 1.25
    pad_1_y = pitch * (circuits - 1) / 2
    pads_x = origin_x + 0.8
    for i in range(circuits):
        pad_name = str(i + 1)
        uuid_pkg_pad = _uuid(f'pad-{i + 1:02}')
        uuid_fpt_pad = _uuid(f'default-pad-{i + 1:02}')
        package.add_pad(PackagePad(uuid=uuid_pkg_pad, name=Name(pad_name)))
        y = pad_1_y - (i * pitch)
        footprint.add_pad(
            FootprintPad(
                uuid=uuid_fpt_pad,
                side=ComponentSide.TOP,
                shape=Shape.ROUNDED_RECT,
                position=Position(pads_x, y),
                rotation=Rotation(0),
                size=Size(1.6, 0.8),
                radius=ShapeRadius(0.0),
                stop_mask=StopMaskConfig(StopMaskConfig.AUTO),
                solder_paste=SolderPasteConfig.AUTO,
                copper_clearance=CopperClearance(0),
                function=PadFunction.STANDARD_PAD,
                package_pad=PackagePadUuid(uuid_pkg_pad),
                holes=[],
            )
        )
        top = y + 0.16
        bottom = y - 0.16
        left = origin_x
        right = origin_x + 1.0
        footprint.add_polygon(
            Polygon(
                uuid=_uuid(f'default-polygon-documentation-{pad_name}'),
                layer=Layer('top_documentation'),
                width=Width(0),
                fill=Fill(True),
                grab_area=GrabArea(False),
                vertices=[
                    Vertex(Position(left, bottom), Angle(0)),
                    Vertex(Position(left, top), Angle(0)),
                    Vertex(Position(right, top), Angle(0)),
                    Vertex(Position(right, bottom), Angle(0)),
                    Vertex(Position(left, bottom), Angle(0)),
                ],
            )
        )

    # Mechanical pads
    pads_height = 2.1
    pads_outer_dy = 3.6 + (circuits - 1) * pitch / 2
    pads_x = origin_x - 1.0 - (2.2 / 2)
    pads_dy = pads_outer_dy - (pads_height / 2)
    for pad_name, polygon_name, side in [('TAB1', 'top', 1), ('TAB2', 'bottom', -1)]:
        uuid_pkg_pad = _uuid(f'pad-{pad_name}')
        uuid_fpt_pad = _uuid(f'default-pad-{pad_name}')
        package.add_pad(PackagePad(uuid=uuid_pkg_pad, name=Name(pad_name)))
        footprint.add_pad(
            FootprintPad(
                uuid=uuid_fpt_pad,
                side=ComponentSide.TOP,
                shape=Shape.ROUNDED_RECT,
                position=Position(pads_x, pads_dy * side),
                rotation=Rotation(0),
                size=Size(3.0, pads_height),
                radius=ShapeRadius(0.0),
                stop_mask=StopMaskConfig(StopMaskConfig.AUTO),
                solder_paste=SolderPasteConfig.AUTO,
                copper_clearance=CopperClearance(0),
                function=PadFunction.STANDARD_PAD,
                package_pad=PackagePadUuid(uuid_pkg_pad),
                holes=[],
            )
        )
        top = (pad_1_y + 3.0 - (LINE_WIDTH / 2)) * side
        bottom = (pad_1_y + 1.5 - (LINE_WIDTH / 2)) * side
        left = origin_x - 3.8 + (LINE_WIDTH / 2)
        right = origin_x - 3.2
        footprint.add_polygon(
            Polygon(
                uuid=_uuid(f'default-polygon-documentation-{polygon_name}'),
                layer=Layer('top_documentation'),
                width=Width(LINE_WIDTH),
                fill=Fill(False),
                grab_area=GrabArea(False),
                vertices=[
                    Vertex(Position(left, bottom), Angle(0)),
                    Vertex(Position(left, top), Angle(0)),
                    Vertex(Position(right, top), Angle(0)),
                ],
            )
        )
        top = (pad_1_y + 3.2) * side
        bottom = (pad_1_y + 1.5) * side
        left = origin_x - 3.2
        right = origin_x - 1.0
        footprint.add_polygon(
            Polygon(
                uuid=_uuid(f'default-polygon-documentation-{pad_name}'),
                layer=Layer('top_documentation'),
                width=Width(0),
                fill=Fill(True),
                grab_area=GrabArea(False),
                vertices=[
                    Vertex(Position(left, bottom), Angle(0)),
                    Vertex(Position(left, top), Angle(0)),
                    Vertex(Position(right, top), Angle(0)),
                    Vertex(Position(right, bottom), Angle(0)),
                    Vertex(Position(left, bottom), Angle(0)),
                ],
            )
        )

    # Documentation body
    dy = pad_1_y + 1.5 - (LINE_WIDTH / 2)
    left = origin_x - 4.2 + (LINE_WIDTH / 2)
    right = origin_x - (LINE_WIDTH / 2)
    footprint.add_polygon(
        Polygon(
            uuid=_uuid('default-polygon-documentation-body'),
            layer=Layer('top_documentation'),
            width=Width(LINE_WIDTH),
            fill=Fill(False),
            grab_area=GrabArea(False),
            vertices=[
                Vertex(Position(left, dy), Angle(0)),
                Vertex(Position(right, dy), Angle(0)),
                Vertex(Position(right, -dy), Angle(0)),
                Vertex(Position(left, -dy), Angle(0)),
                Vertex(Position(left, dy), Angle(0)),
            ],
        )
    )

    # Legend outline
    dy_leg = pad_1_y + 3.0 - (LINE_WIDTH / 2)
    dy_body = pad_1_y + 1.5 + (LINE_WIDTH / 2)
    x0_body = origin_x - 4.2 - (LINE_WIDTH / 2)
    x1_leg = origin_x - 3.8 - (LINE_WIDTH / 2)
    footprint.add_polygon(
        Polygon(
            uuid=_uuid('default-polygon-legend-left'),
            layer=Layer('top_legend'),
            width=Width(LINE_WIDTH),
            fill=Fill(False),
            grab_area=GrabArea(False),
            vertices=[
                Vertex(Position(x1_leg, dy_leg), Angle(0)),
                Vertex(Position(x1_leg, dy_body), Angle(0)),
                Vertex(Position(x0_body, dy_body), Angle(0)),
                Vertex(Position(x0_body, -dy_body), Angle(0)),
                Vertex(Position(x1_leg, -dy_body), Angle(0)),
                Vertex(Position(x1_leg, -dy_leg), Angle(0)),
            ],
        )
    )
    x0_leg = origin_x - 0.6 + 0.15 + (LINE_WIDTH / 2)
    x1_body = origin_x + (LINE_WIDTH / 2)
    x2_pin = origin_x + 1.0 - (LINE_WIDTH / 2)
    dy_pad = pad_1_y + 0.4 + 0.15 + (LINE_WIDTH / 2)
    footprint.add_polygon(
        Polygon(
            uuid=_uuid('default-polygon-legend-top'),
            layer=Layer('top_legend'),
            width=Width(LINE_WIDTH),
            fill=Fill(False),
            grab_area=GrabArea(False),
            vertices=[
                Vertex(Position(x0_leg, dy_body), Angle(0)),
                Vertex(Position(x1_body, dy_body), Angle(0)),
                Vertex(Position(x1_body, dy_pad), Angle(0)),
                Vertex(Position(x2_pin, dy_pad), Angle(0)),
            ],
        )
    )
    footprint.add_polygon(
        Polygon(
            uuid=_uuid('default-polygon-legend-bottom'),
            layer=Layer('top_legend'),
            width=Width(LINE_WIDTH),
            fill=Fill(False),
            grab_area=GrabArea(False),
            vertices=[
                Vertex(Position(x0_leg, -dy_body), Angle(0)),
                Vertex(Position(x1_body, -dy_body), Angle(0)),
                Vertex(Position(x1_body, -dy_pad), Angle(0)),
            ],
        )
    )

    # Pin-1 dot
    footprint.add_circle(
        Circle(
            uuid=_uuid('default-circle-documentation-pin1'),
            layer=Layer('top_documentation'),
            width=Width(0),
            fill=Fill(True),
            grab_area=GrabArea(False),
            diameter=Diameter(0.8),
            position=Position(origin_x - 0.9, pad_1_y + 1.5 - 0.9),
        )
    )

    # Package outline
    dy_leg = pad_1_y + 3.2
    dy_body = pad_1_y + 1.5
    dy_pin = pad_1_y + 0.16
    x0_body = origin_x - 4.2
    x1_leg = origin_x - 3.8
    x2_leg = origin_x - 1.0
    x3_body = origin_x
    x4_pin = origin_x + 1.0
    footprint.add_polygon(
        Polygon(
            uuid=_uuid('default-polygon-outline'),
            layer=Layer('top_package_outlines'),
            width=Width(0),
            fill=Fill(False),
            grab_area=GrabArea(False),
            vertices=[
                Vertex(Position(x0_body, dy_body), Angle(0)),
                Vertex(Position(x1_leg, dy_body), Angle(0)),
                Vertex(Position(x1_leg, dy_leg), Angle(0)),
                Vertex(Position(x2_leg, dy_leg), Angle(0)),
                Vertex(Position(x2_leg, dy_body), Angle(0)),
                Vertex(Position(x3_body, dy_body), Angle(0)),
                Vertex(Position(x3_body, dy_pin), Angle(0)),
                Vertex(Position(x4_pin, dy_pin), Angle(0)),
                Vertex(Position(x4_pin, -dy_pin), Angle(0)),
                Vertex(Position(x3_body, -dy_pin), Angle(0)),
                Vertex(Position(x3_body, -dy_body), Angle(0)),
                Vertex(Position(x2_leg, -dy_body), Angle(0)),
                Vertex(Position(x2_leg, -dy_leg), Angle(0)),
                Vertex(Position(x1_leg, -dy_leg), Angle(0)),
                Vertex(Position(x1_leg, -dy_body), Angle(0)),
                Vertex(Position(x0_body, -dy_body), Angle(0)),
            ],
        )
    )

    # Courtyard
    dy_leg = pad_1_y + 3.2 + COURTYARD_EXCESS
    dy_body = pad_1_y + 1.5 + COURTYARD_EXCESS
    dy_pin = pad_1_y + 0.16 + COURTYARD_EXCESS
    x0_body = origin_x - 4.2 - COURTYARD_EXCESS
    x1_leg = origin_x - 3.8 - COURTYARD_EXCESS
    x2_leg = origin_x - 1.0 + COURTYARD_EXCESS
    x3_body = origin_x + COURTYARD_EXCESS
    x4_pin = origin_x + 1.0 + COURTYARD_EXCESS
    footprint.add_polygon(
        Polygon(
            uuid=_uuid('default-polygon-courtyard'),
            layer=Layer('top_courtyard'),
            width=Width(0),
            fill=Fill(False),
            grab_area=GrabArea(False),
            vertices=[
                Vertex(Position(x0_body, dy_body), Angle(0)),
                Vertex(Position(x1_leg, dy_body), Angle(0)),
                Vertex(Position(x1_leg, dy_leg), Angle(0)),
                Vertex(Position(x2_leg, dy_leg), Angle(0)),
                Vertex(Position(x2_leg, dy_body), Angle(0)),
                Vertex(Position(x3_body, dy_body), Angle(0)),
                Vertex(Position(x3_body, dy_pin), Angle(0)),
                Vertex(Position(x4_pin, dy_pin), Angle(0)),
                Vertex(Position(x4_pin, -dy_pin), Angle(0)),
                Vertex(Position(x3_body, -dy_pin), Angle(0)),
                Vertex(Position(x3_body, -dy_body), Angle(0)),
                Vertex(Position(x2_leg, -dy_body), Angle(0)),
                Vertex(Position(x2_leg, -dy_leg), Angle(0)),
                Vertex(Position(x1_leg, -dy_leg), Angle(0)),
                Vertex(Position(x1_leg, -dy_body), Angle(0)),
                Vertex(Position(x0_body, -dy_body), Angle(0)),
            ],
        )
    )

    # Labels
    top = pad_1_y + 3.6
    bottom = -top
    footprint.add_text(
        StrokeText(
            uuid=_uuid('default-text-name'),
            layer=Layer('top_names'),
            height=Height(1.0),
            stroke_width=StrokeWidth(0.2),
            letter_spacing=LetterSpacing.AUTO,
            line_spacing=LineSpacing.AUTO,
            align=Align('center bottom'),
            position=Position(0.0, top + 0.4),
            rotation=Rotation(0.0),
            auto_rotate=AutoRotate(True),
            mirror=Mirror(False),
            value=Value('{{NAME}}'),
        )
    )
    footprint.add_text(
        StrokeText(
            uuid=_uuid('default-text-value'),
            layer=Layer('top_values'),
            height=Height(1.0),
            stroke_width=StrokeWidth(0.2),
            letter_spacing=LetterSpacing.AUTO,
            line_spacing=LineSpacing.AUTO,
            align=Align('center top'),
            position=Position(0.0, bottom - 0.4),
            rotation=Rotation(0.0),
            auto_rotate=AutoRotate(True),
            mirror=Mirror(False),
            value=Value('{{VALUE}}'),
        )
    )

    # Generate 3D model
    uuid_3d = _uuid('3d')
    if generate_3d_models:
        generate_3d_model(library, name, uuid_pkg, uuid_3d, circuits, origin_x)
    package.add_3d_model(Package3DModel(uuid_3d, Name(name)))
    for footprint in package.footprints:
        footprint.add_3d_model(Footprint3DModel(uuid_3d))

    package.serialize(path.join('out', library, 'pkg'))


def generate_3d_model(
    library: str,
    full_name: str,
    uuid_pkg: str,
    uuid_3d: str,
    circuits: int,
    origin_x: float,
) -> None:
    import cadquery as cq

    from cadquery_helpers import StepAssembly, StepColor

    print(f'Generating pkg 3D model "{full_name}": {uuid_3d}')

    assembly = StepAssembly(full_name)

    # Body
    width = 4.2
    length = (circuits - 1) * 1.25 + 3.0
    height = 3.4
    legs_width = 2.8
    legs_length = (circuits - 1) * 1.25 + 6.0
    legs_height = 2.0  # guessed
    legs_standoff = 0.4  # guessed
    body = cq.Workplane('XY').box(width, length, height, centered=(True, True, False))
    body = (
        body.workplane(origin=(0.4 - width / 2, 0, 0), offset=legs_standoff - height / 2)
        .box(legs_width, legs_length, legs_height, centered=(False, True, False))
        .edges('>Y or <Y')
        .chamfer(0.3)
    )
    body = body.cut(
        cq.Workplane('XY', origin=(origin_x - 2.6 - 10, 0, 0.6)).box(
            10, length - 0.8, 10, centered=(False, True, False)
        )
    )
    body = body.cut(
        cq.Workplane('YZ', origin=(-10, 0, 0.6)).box(
            length - 0.8, 2.4, 10 + (width / 2) - 1, centered=(True, False, False)
        )
    )
    assembly.add_body(
        body, 'body', cq.Color('gray95'), location=cq.Location((origin_x - (width / 2), 0, 0))
    )

    # Legs
    pitch = 1.25
    pad_1_y = pitch * (circuits - 1) / 2
    leg = (
        cq.Workplane('XZ')
        .moveTo(-3.5, 1.0)
        .lineTo(-3.5, 1.5)
        .lineTo(-0.1, 1.5)
        .lineTo(-0.1, 1.375)
        .lineTo(0.7, 1.375)
        .lineTo(0.7, 0.5)
        .lineTo(1.0, 0.5)
        .lineTo(1.0, 0.2)
        .lineTo(0.8, 0.0)
        .lineTo(0.4, 0.0)
        .lineTo(0.2, 0.2)
        .lineTo(0.2, 1.0)
        .close()
        .extrude(0.32)
    )
    for i in range(circuits):
        y = pad_1_y - (i * pitch)
        assembly.add_body(
            leg, f'leg-{i + 1}', StepColor.LEAD_SMT, location=cq.Location((origin_x, y + 0.16, 0))
        )

    # Mechanical leads
    mpad_length = (circuits - 1) * 1.25 + 6.4
    mpad = cq.Workplane('XY').box(2.2, mpad_length, 0.25, centered=(True, True, False))
    assembly.add_body(
        mpad, 'tabs', StepColor.LEAD_SMT, location=cq.Location((origin_x - 2.1, 0, 0))
    )

    # Save without fusing for massively better minification!
    out_path = path.join('out', library, 'pkg', uuid_pkg, f'{uuid_3d}.step')
    assembly.save(out_path, fused=False)


def generate_dev(
    library: str,
    author: str,
    version: str,
    create_date: Optional[str],
    uuid_key: str,
    circuits: int,
    name: str,
    description: str,
    keywords: str,
    categories: List[str],
    datasheet: str,
    parts: List[Part],
) -> None:
    def _uuid(identifier: str) -> str:
        return uuid('dev', uuid_key, identifier)

    uuid_dev = _uuid('dev')

    print(f'Generating {name}: {uuid_dev}')

    connector_uuid_stub = f'cmp-pinheader-1x{circuits}'
    component_uuid = uuid_cache_connectors[f'{connector_uuid_stub}-cmp']
    signal_uuids = [
        uuid_cache_connectors[f'{connector_uuid_stub}-signal-{i}'] for i in range(circuits)
    ]

    device = Device(
        uuid=uuid_dev,
        name=Name(name),
        description=Description(description + f'\n\nGenerated with {generator}'),
        keywords=Keywords(keywords),
        author=Author(author),
        version=Version(version),
        created=Created(create_date or now()),
        deprecated=Deprecated(False),
        generated_by=GeneratedBy(''),
        categories=[Category(c) for c in categories],
        component_uuid=ComponentUUID(component_uuid),
        package_uuid=PackageUUID(uuid('pkg', uuid_key, 'pkg')),
    )

    for i in range(circuits):
        pad_uuid = uuid_cache[f'pkg-{uuid_key}-pad-{i + 1:02}']
        device.add_pad(ComponentPad(pad_uuid, SignalUUID(signal_uuids[i])))
    for i in range(2):
        pad_uuid = uuid_cache[f'pkg-{uuid_key}-pad-tab{i + 1}']
        device.add_pad(ComponentPad(pad_uuid, SignalUUID('none')))

    device.add_resource(
        Resource(
            name='Datasheet {}'.format(name),
            mediatype='application/pdf',
            url=datasheet,
        )
    )

    for part in parts:
        device.add_part(part)

    device.serialize(path.join('out', library, 'dev'))


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

    for circuits in range(2, 18):
        description = (
            f'Picoblade, SMT, right-angle, {circuits}-pin, 1.25mm wire-to-board connector.'
        )
        generate_pkg(
            library='Molex.lplib',
            author='U. Bruhin',
            version='0.1',
            create_date='2026-01-21T10:30:49Z',
            uuid_key=f'53261-{circuits:02}',
            circuits=circuits,
            name=f'MOLEX_53261-{circuits:02}',
            description=description,
            keywords='picoblade',
            categories=['2da719e9-d7e0-4c7e-b0dd-fd04d8806f97'],
            generate_3d_models=generate_3d_models,
        )
        parts = [
            Part(
                f'53261-{circuits:02}71',
                Manufacturer('Molex'),
                [
                    Attribute('PLATING', 'Tin', AttributeType.STRING, None),
                ],
            )
        ]
        if circuits <= 15:
            parts.append(
                Part(
                    f'53261-40{circuits:02}',
                    Manufacturer('Molex'),
                    [
                        Attribute('PLATING', 'Gold', AttributeType.STRING, None),
                    ],
                )
            )
        generate_dev(
            library='Molex.lplib',
            author='U. Bruhin',
            version='0.1',
            create_date='2026-01-21T10:30:49Z',
            uuid_key=f'53261-{circuits:02}',
            circuits=circuits,
            name=f'Molex 53261-{circuits:02}',
            description=description,
            keywords='picoblade',
            categories=['4a4e3c72-94fb-45f9-a6d8-122d2af16fb1'],
            datasheet=f'https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/532/53261/53261{circuits:02}71_sd.pdf',
            parts=parts,
        )

    save_cache(uuid_cache_file, uuid_cache)
