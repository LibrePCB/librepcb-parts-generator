"""
Generate screw terminal packages & devices
"""

import math
import sys
from os import path
from uuid import uuid4

from typing import Any, Callable, List, Optional

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
from entities.device import ComponentPad, ComponentUUID, Device, Manufacturer, PackageUUID, Part
from entities.package import (
    AssemblyType,
    AutoRotate,
    ComponentSide,
    CopperClearance,
    DrillDiameter,
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
    PadHole,
    Shape,
    ShapeRadius,
    Size,
    SolderPasteConfig,
    StopMaskConfig,
    StrokeText,
    StrokeWidth,
)

generator = 'librepcb-parts-generator (generate_screw_terminals.py)'

line_width = 0.2
courtyard_excess = 0.4


# Initialize UUID cache
uuid_cache_file = 'uuid_cache_screw_terminals.csv'
uuid_cache = init_cache(uuid_cache_file)

uuid_cache_connectors = init_cache('uuid_cache_connectors.csv')


def uuid(category: str, full_name: str, identifier: str) -> str:
    key = '{}-{}-{}'.format(category, full_name, identifier).lower().replace(' ', '~')
    if key not in uuid_cache:
        uuid_cache[key] = str(uuid4())
    return uuid_cache[key]


def create_screw_diagonal(y: float, diameter: float, dir: int) -> List[Vertex]:
    dx = (diameter / 2) * math.cos(math.radians(45 + 12 * dir))
    dy = (diameter / 2) * math.sin(math.radians(45 + 12 * dir))
    return [
        Vertex(Position(dx, y + dy), Angle(0)),
        Vertex(Position(-dy, y - dx), Angle(0)),
    ]


class Nipple:
    def __init__(self, x: float, width: float, height: float):
        self.x = x
        self.width = width
        self.height = height


class Family:
    def __init__(
        self,
        manufacturer: str,
        pkg_name_prefix: str,
        dev_name_prefix: str,
        pitch: float,
        drill: float,
        pad_diameter: float,
        top: float,
        bottom: float,
        left: float,
        right: float,
        height: float,
        lead_diameter: float,
        lead_length: float,
        opening_width_bottom: float,
        opening_width: float,
        opening_height: float,
        screw_hole_diameter: float,
        conductor_cross_section: str,
        walls_length: float,
        nipples_bottom: List[Nipple],
        datasheet: Optional[str],
        keywords: List[str],
        draw_body_sketch_fn: Callable[[Any], Any],
    ) -> None:
        self.manufacturer = manufacturer
        self.pkg_name_prefix = pkg_name_prefix
        self.dev_name_prefix = dev_name_prefix
        self.pitch = pitch
        self.drill = drill
        self.pad_diameter = pad_diameter
        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right
        self.height = height
        self.lead_diameter = lead_diameter
        self.lead_length = lead_length
        self.opening_width_bottom = opening_width_bottom
        self.opening_width = opening_width
        self.opening_height = opening_height
        self.screw_hole_diameter = screw_hole_diameter
        self.conductor_cross_section = conductor_cross_section
        self.walls_length = walls_length
        self.nipples_bottom = nipples_bottom
        self.datasheet = datasheet
        self.keywords = keywords
        self.draw_body_sketch_fn = draw_body_sketch_fn


class Model:
    def __init__(self, name: str, mpn: str, circuits: int, datasheet: Optional[str] = None) -> None:
        self.name = name
        self.mpn = mpn
        self.circuits = circuits
        self.datasheet = datasheet

    def uuid_key(self, family: Family) -> str:
        return (
            '{}-{}'.format(family.pkg_name_prefix, model.name)
            .lower()
            .replace(' ', '')
            .replace(',', 'p')
        )

    def get_description(self, family: Family) -> str:
        return f"""Screw terminal from {family.manufacturer}:

Circuits: {self.circuits}
Pitch: {family.pitch:.2f} mm
Height: {family.height:.2f} mm
Conductor: {family.conductor_cross_section}

Generated with {generator}
"""

    def get_keywords(self, family: Family) -> str:
        return ','.join(
            [
                'screw',
                'terminal',
                'block',
                '{:g}mm'.format(family.pitch),
                '1x{}'.format(self.circuits),
            ]
            + family.keywords
        )

    def get_datasheet(self, family: Family) -> Optional[str]:
        ds = self.datasheet
        if ds is None:
            ds = family.datasheet
        if ds is None:
            return None
        return ds.format(mpn=self.mpn)


def generate_pkg(
    library: str,
    author: str,
    version: str,
    create_date: Optional[str],
    family: Family,
    model: Model,
    generate_3d_models: bool,
) -> None:
    full_name = family.pkg_name_prefix + '_' + model.name.replace(' ', '_')

    def _uuid(identifier: str) -> str:
        return uuid('pkg', model.uuid_key(family), identifier)

    uuid_pkg = _uuid('pkg')

    print('Generating {}: {}'.format(full_name, uuid_pkg))

    package = Package(
        uuid=uuid_pkg,
        name=Name(full_name),
        description=Description(model.get_description(family)),
        keywords=Keywords(model.get_keywords(family)),
        author=Author(author),
        version=Version(version),
        created=Created(create_date or now()),
        deprecated=Deprecated(False),
        generated_by=GeneratedBy(''),
        categories=[Category('b724b55e-0f80-4cf3-aa9f-e2a87e02bd19')],
        assembly_type=AssemblyType.THT,
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

    # Pads
    pad_1_y = family.pitch * (model.circuits - 1) / 2
    for i in range(model.circuits):
        pad_name = str(i + 1)
        uuid_pkg_pad = _uuid('pad-{}'.format(pad_name))
        uuid_fpt_pad = _uuid('default-pad-{}'.format(pad_name))
        package.add_pad(PackagePad(uuid=uuid_pkg_pad, name=Name(pad_name)))
        y = pad_1_y - (i * family.pitch)
        footprint.add_pad(
            FootprintPad(
                uuid=uuid_fpt_pad,
                side=ComponentSide.TOP,
                shape=Shape.ROUNDED_RECT,
                position=Position(0, y),
                rotation=Rotation(0),
                size=Size(family.pad_diameter, family.pad_diameter),
                radius=ShapeRadius(0.0 if (i == 0) else 1.0),
                stop_mask=StopMaskConfig(StopMaskConfig.AUTO),
                solder_paste=SolderPasteConfig.OFF,
                copper_clearance=CopperClearance(0),
                function=PadFunction.STANDARD_PAD,
                package_pad=PackagePadUuid(uuid_pkg_pad),
                holes=[
                    PadHole(
                        uuid_fpt_pad,
                        DrillDiameter(family.drill),
                        [Vertex(Position(0.0, 0.0), Angle(0.0))],
                    )
                ],
            )
        )
        footprint.add_circle(
            Circle(
                uuid=_uuid('default-circle-{}'.format(pad_name)),
                layer=Layer('top_documentation'),
                width=Width(line_width * 0.75),
                fill=Fill(False),
                grab_area=GrabArea(False),
                diameter=Diameter(family.screw_hole_diameter),
                position=Position(0, y),
            )
        )
        footprint.add_polygon(
            Polygon(
                uuid=_uuid('default-screw-upper-{}'.format(pad_name)),
                layer=Layer('top_documentation'),
                width=Width(line_width * 0.75),
                fill=Fill(False),
                grab_area=GrabArea(False),
                vertices=create_screw_diagonal(y, family.screw_hole_diameter, 1),
            )
        )
        footprint.add_polygon(
            Polygon(
                uuid=_uuid('default-screw-lower-{}'.format(pad_name)),
                layer=Layer('top_documentation'),
                width=Width(line_width * 0.75),
                fill=Fill(False),
                grab_area=GrabArea(False),
                vertices=create_screw_diagonal(y, family.screw_hole_diameter, -1),
            )
        )

    # Documentation outline
    top = pad_1_y + family.top - (line_width / 2)
    bottom = -pad_1_y - family.bottom + (line_width / 2)
    left = -family.left + (line_width / 2)
    right = family.right - (line_width / 2)
    footprint.add_polygon(
        Polygon(
            uuid=_uuid('default-polygon-documentation'),
            layer=Layer('top_documentation'),
            width=Width(line_width),
            fill=Fill(False),
            grab_area=GrabArea(False),
            vertices=[
                Vertex(Position(left, top), Angle(0)),
                Vertex(Position(right, top), Angle(0)),
                Vertex(Position(right, bottom), Angle(0)),
                Vertex(Position(left, bottom), Angle(0)),
                Vertex(Position(left, top), Angle(0)),
            ],
        )
    )

    # Documentation walls
    if family.walls_length > 0:
        walls_dy = family.pitch - family.opening_width
        for i in range(model.circuits + 1):
            y = pad_1_y + (family.pitch / 2) - (i * family.pitch)
            top = min(y + walls_dy / 2, pad_1_y + family.top - (line_width / 2))
            bottom = max(y - walls_dy / 2, -pad_1_y - family.bottom + (line_width / 2))
            left = -family.left - family.walls_length
            right = -family.left
            footprint.add_polygon(
                Polygon(
                    uuid=_uuid('default-polygon-documentation-wall-{}'.format(i + 1)),
                    layer=Layer('top_documentation'),
                    width=Width(0),
                    fill=Fill(True),
                    grab_area=GrabArea(False),
                    vertices=[
                        Vertex(Position(left, top), Angle(0)),
                        Vertex(Position(right, top), Angle(0)),
                        Vertex(Position(right, bottom), Angle(0)),
                        Vertex(Position(left, bottom), Angle(0)),
                        Vertex(Position(left, top), Angle(0)),
                    ],
                )
            )

    # Documentation nipples
    for i, nipple in enumerate(family.nipples_bottom):
        top = -pad_1_y - family.bottom
        bottom = top - nipple.height
        left = nipple.x - (nipple.width / 2)
        right = nipple.x + (nipple.width / 2)
        footprint.add_polygon(
            Polygon(
                uuid=_uuid('default-polygon-documentation-nipple-bottom-{}'.format(i + 1)),
                layer=Layer('top_documentation'),
                width=Width(0),
                fill=Fill(True),
                grab_area=GrabArea(False),
                vertices=[
                    Vertex(Position(left, top), Angle(0)),
                    Vertex(Position(right, top), Angle(0)),
                    Vertex(Position(right, bottom), Angle(0)),
                    Vertex(Position(left, bottom), Angle(0)),
                    Vertex(Position(left, top), Angle(0)),
                ],
            )
        )

    # Legend outline
    top = pad_1_y + family.top + (line_width / 2)
    bottom = -pad_1_y - family.bottom - (line_width / 2)
    left = -family.left - (line_width / 2)
    right = family.right + (line_width / 2)
    dy = pad_1_y + (family.opening_width_bottom / 2) + (line_width / 2)
    legend_outline_vertices = [
        Vertex(Position(left, dy), Angle(0)),
        Vertex(Position(left, top), Angle(0)),
        Vertex(Position(right, top), Angle(0)),
        Vertex(Position(right, bottom), Angle(0)),
    ]
    for nipple in reversed(family.nipples_bottom):
        nipple_dx = (nipple.width / 2) + (line_width / 2)
        nipple_dy = nipple.height
        legend_outline_vertices += [
            Vertex(Position(nipple.x + nipple_dx, bottom), Angle(0)),
            Vertex(Position(nipple.x + nipple_dx, bottom - nipple_dy), Angle(0)),
            Vertex(Position(nipple.x - nipple_dx, bottom - nipple_dy), Angle(0)),
            Vertex(Position(nipple.x - nipple_dx, bottom), Angle(0)),
        ]
    legend_outline_vertices += [
        Vertex(Position(left, bottom), Angle(0)),
        Vertex(Position(left, -dy), Angle(0)),
    ]
    footprint.add_polygon(
        Polygon(
            uuid=_uuid('default-polygon-legend'),
            layer=Layer('top_legend'),
            width=Width(line_width),
            fill=Fill(False),
            grab_area=GrabArea(False),
            vertices=legend_outline_vertices,
        )
    )
    for i in range(model.circuits - 1):
        top = pad_1_y - (i * family.pitch) - (family.opening_width_bottom / 2)
        bottom = top - (family.pitch - family.opening_width_bottom)
        footprint.add_polygon(
            Polygon(
                uuid=_uuid('default-polygon-legend-{}'.format(i + 1)),
                layer=Layer('top_legend'),
                width=Width(line_width),
                fill=Fill(False),
                grab_area=GrabArea(False),
                vertices=[
                    Vertex(Position(left, top - (line_width / 2)), Angle(0)),
                    Vertex(Position(left, bottom + (line_width / 2)), Angle(0)),
                ],
            )
        )

    # Pin-1 marking
    triangle_right = -family.screw_hole_diameter / 2
    for layer in ['legend', 'documentation']:
        footprint.add_polygon(
            Polygon(
                uuid=_uuid('default-triangle-' + layer),
                layer=Layer('top_' + layer),
                width=Width(0),
                fill=Fill(True),
                grab_area=GrabArea(False),
                vertices=[
                    Vertex(Position(triangle_right - 0.7, pad_1_y + 0.6), Angle(0)),
                    Vertex(Position(triangle_right, pad_1_y), Angle(0)),
                    Vertex(Position(triangle_right - 0.7, pad_1_y - 0.6), Angle(0)),
                    Vertex(Position(triangle_right - 0.7, pad_1_y + 0.6), Angle(0)),
                ],
            )
        )

    # Package outline
    top = pad_1_y + family.top
    bottom = -pad_1_y - family.bottom
    left = -family.left
    right = family.right
    footprint.add_polygon(
        Polygon(
            uuid=_uuid('default-polygon-outline'),
            layer=Layer('top_package_outlines'),
            width=Width(0),
            fill=Fill(False),
            grab_area=GrabArea(False),
            vertices=[
                Vertex(Position(left, top), Angle(0)),
                Vertex(Position(right, top), Angle(0)),
                Vertex(Position(right, bottom), Angle(0)),
                Vertex(Position(left, bottom), Angle(0)),
            ],
        )
    )

    # Courtyard
    top = max(legend_outline_vertices, key=lambda v: v.position.y).position.y
    top += courtyard_excess - (line_width / 2)
    bottom = min(legend_outline_vertices, key=lambda v: v.position.y).position.y
    bottom -= courtyard_excess - (line_width / 2)
    left = -family.left - family.walls_length - courtyard_excess
    right = family.right + courtyard_excess
    footprint.add_polygon(
        Polygon(
            uuid=_uuid('default-polygon-courtyard'),
            layer=Layer('top_courtyard'),
            width=Width(0),
            fill=Fill(False),
            grab_area=GrabArea(False),
            vertices=[
                Vertex(Position(left, top), Angle(0)),
                Vertex(Position(right, top), Angle(0)),
                Vertex(Position(right, bottom), Angle(0)),
                Vertex(Position(left, bottom), Angle(0)),
            ],
        )
    )

    # Labels
    top = max(legend_outline_vertices, key=lambda v: v.position.y).position.y
    bottom = min(legend_outline_vertices, key=lambda v: v.position.y).position.y
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
        generate_3d_model(library, full_name, uuid_pkg, uuid_3d, family, model)
    package.add_3d_model(Package3DModel(uuid_3d, Name(full_name)))
    for footprint in package.footprints:
        footprint.add_3d_model(Footprint3DModel(uuid_3d))

    package.serialize(path.join('out', library, 'pkg'))


def generate_3d_model(
    library: str,
    full_name: str,
    uuid_pkg: str,
    uuid_3d: str,
    family: Family,
    model: Model,
) -> None:
    import cadquery as cq

    from cadquery_helpers import StepAssembly, StepColor

    print(f'Generating pkg 3D model "{full_name}": {uuid_3d}')

    pad1_y = ((model.circuits - 1) * family.pitch) / 2
    body_length = 2 * pad1_y + family.top + family.bottom

    body = cq.Workplane('XZ').transformed(offset=(0, 0, -pad1_y - family.bottom)).tag('top')
    body = family.draw_body_sketch_fn(body).close().extrude(body_length)
    for nipple in family.nipples_bottom:
        body = (
            body.workplaneFromTagged('top')
            .workplane(offset=body_length)
            .transformed(offset=(nipple.x, family.height - 1.5, 0))
            .box(nipple.width, 3.0, 2 * nipple.height, centered=True)
        )
    for i in range(model.circuits):
        y = pad1_y - (i * family.pitch)
        body = body.cut(
            cq.Workplane('XY', origin=(0.0, y, 0.0)).cylinder(100, family.screw_hole_diameter / 2)
        )
        body = body.cut(
            cq.Workplane('YZ', origin=(-family.left, y, (family.opening_height / 2) + 0.5)).box(
                family.opening_width, family.opening_height - 1.0, 2 * family.left
            )
        )
        body = body.cut(
            cq.Workplane('YZ', origin=(-family.left, y, 0.0)).box(
                family.opening_width_bottom, 2.2, 2 * family.left
            )
        )

    screw = (
        cq.Workplane('XY')
        .tag('bottom')
        .cylinder(family.height - 0.2, family.screw_hole_diameter / 2, centered=(True, True, False))
        .workplane(offset=(family.height / 2))
        .box(100, family.screw_hole_diameter * 0.2, 1.0, combine='cut')
        .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 45.0)
        .workplaneFromTagged('bottom')
        .workplane(offset=(((family.opening_height - 1.5) / 2) + 1.0))
        .box(100, family.opening_width - 0.8, family.opening_height - 4.0, combine='cut')
    )
    leg = (
        cq.Workplane('XY')
        .workplane(offset=(-1), invert=True)
        .cylinder(family.lead_length + 1, family.lead_diameter / 2, centered=(True, True, False))
    )

    assembly = StepAssembly(full_name)
    assembly.add_body(body, 'body', cq.Color('green3'))
    for i in range(model.circuits):
        y = pad1_y - (i * family.pitch)
        assembly.add_body(
            screw, 'screw-{}'.format(i + 1), StepColor.LEAD_THT, location=cq.Location((0, y, 0))
        )
        assembly.add_body(
            leg, 'leg-{}'.format(i + 1), StepColor.LEAD_THT, location=cq.Location((0, y, 0))
        )

    # Save without fusing for massively better minification!
    out_path = path.join('out', library, 'pkg', uuid_pkg, f'{uuid_3d}.step')
    assembly.save(out_path, fused=False)


def generate_dev(
    library: str,
    author: str,
    version: str,
    create_date: Optional[str],
    family: Family,
    model: Model,
) -> None:
    full_name = f'{family.dev_name_prefix} {model.name}'

    def _uuid(identifier: str) -> str:
        return uuid('dev', model.uuid_key(family), identifier)

    uuid_dev = _uuid('dev')

    print('Generating {}: {}'.format(full_name, uuid_dev))

    connector_uuid_stub = f'cmp-screwterminal-1x{model.circuits}'
    component_uuid = uuid_cache_connectors[f'{connector_uuid_stub}-cmp']
    signal_uuids = [
        uuid_cache_connectors[f'{connector_uuid_stub}-signal-{i}'] for i in range(model.circuits)
    ]

    device = Device(
        uuid=uuid_dev,
        name=Name(full_name),
        description=Description(model.get_description(family)),
        keywords=Keywords(model.get_keywords(family)),
        author=Author(author),
        version=Version(version),
        created=Created(create_date or now()),
        deprecated=Deprecated(False),
        generated_by=GeneratedBy(''),
        categories=[Category('f9db4ef5-2220-462a-adff-deac8402ecf0')],
        component_uuid=ComponentUUID(component_uuid),
        package_uuid=PackageUUID(uuid('pkg', model.uuid_key(family), 'pkg')),
    )

    for i in range(model.circuits):
        pad_uuid = uuid('pkg', model.uuid_key(family), 'pad-{}'.format(i + 1))
        device.add_pad(ComponentPad(pad_uuid, SignalUUID(signal_uuids[i])))

    device.add_part(
        Part(
            model.mpn,
            Manufacturer(family.manufacturer),
            [
                Attribute('PITCH', f'{family.pitch:.2f} mm', AttributeType.STRING, None),
                Attribute(
                    'CONDUCTOR', f'{family.conductor_cross_section}', AttributeType.STRING, None
                ),
            ],
        )
    )

    datasheet = model.get_datasheet(family)
    if datasheet:
        device.add_resource(
            Resource(
                name='Datasheet {}'.format(model.name),
                mediatype='application/pdf',
                url=datasheet,
            )
        )

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

    # Phoenix PT 1,5/x-5,0-H
    family = Family(
        manufacturer='Phoenix Contact',
        pkg_name_prefix='PHOENIX',
        dev_name_prefix='Phoenix',
        pitch=5.0,
        drill=1.2,  # Officially 1.3mm, but I think that's too loose
        pad_diameter=2.6,
        top=2.5,
        bottom=2.5,
        left=4.3,
        right=4.0,
        height=11.4,
        lead_diameter=1.0,
        lead_length=3.5,
        opening_width_bottom=2.2,  # Measured in STEP model
        opening_width=3.8,  # Measured in STEP model
        opening_height=6.6,  # Guessed
        screw_hole_diameter=4.0,  # Measured in STEP model
        conductor_cross_section='1.5 mm²',
        walls_length=0.7,
        nipples_bottom=[
            Nipple(x=-2.0, width=0.7, height=0.4),
            Nipple(x=2.0, width=0.7, height=0.4),
        ],
        datasheet='https://www.phoenixcontact.com/us/products/{mpn}/pdf',
        keywords=[],
        draw_body_sketch_fn=lambda workplane: workplane.moveTo(4.0, 0.0)
        .lineTo(4.0, 3.5)
        .lineTo(2.5, 11.4)
        .lineTo(-2.5, 11.4)
        .lineTo(-3.8, 6.5)
        .lineTo(-4.5, 6.5)
        .ellipseArc(x_radius=0.5, y_radius=0.5, angle1=90, angle2=180, sense=1)
        .lineTo(-5.0, 4.0)
        .ellipseArc(x_radius=0.5, y_radius=0.5, angle1=180, angle2=270, sense=1)
        .lineTo(-4.3, 3.5)
        .lineTo(-4.3, 0.0),
    )
    models = [
        Model(name='PT 1,5/2-5,0-H', mpn='1935161', circuits=2),
        Model(name='PT 1,5/3-5,0-H', mpn='1935174', circuits=3),
        Model(name='PT 1,5/4-5,0-H', mpn='1935187', circuits=4),
        Model(name='PT 1,5/5-5,0-H', mpn='1935190', circuits=5),
        Model(name='PT 1,5/6-5,0-H', mpn='1935200', circuits=6),
        Model(name='PT 1,5/7-5,0-H', mpn='1935213', circuits=7),
        Model(name='PT 1,5/8-5,0-H', mpn='1935226', circuits=8),
        Model(name='PT 1,5/9-5,0-H', mpn='1935239', circuits=9),
        Model(name='PT 1,5/10-5,0-H', mpn='1935242', circuits=10),
        Model(name='PT 1,5/11-5,0-H', mpn='1935255', circuits=11),
        Model(name='PT 1,5/12-5,0-H', mpn='1935268', circuits=12),
        Model(name='PT 1,5/13-5,0-H', mpn='1935271', circuits=13),
        Model(name='PT 1,5/14-5,0-H', mpn='1935284', circuits=14),
        Model(name='PT 1,5/15-5,0-H', mpn='1935297', circuits=15),
        Model(name='PT 1,5/16-5,0-H', mpn='1935307', circuits=16),
    ]
    for model in models:
        generate_pkg(
            library='Phoenix.lplib',
            author='U. Bruhin',
            version='0.1',
            create_date='2025-04-10T13:33:42Z',
            family=family,
            model=model,
            generate_3d_models=generate_3d_models,
        )
        generate_dev(
            library='Phoenix.lplib',
            author='U. Bruhin',
            version='0.1',
            create_date='2025-04-10T13:33:42Z',
            family=family,
            model=model,
        )

    # Phoenix PT 2,5/x-5,0-H
    family = Family(
        manufacturer='Phoenix Contact',
        pkg_name_prefix='PHOENIX',
        dev_name_prefix='Phoenix',
        pitch=5.0,
        drill=1.2,  # Officially 1.3mm, but I think that's too loose
        pad_diameter=2.6,
        top=2.5,
        bottom=2.5,
        left=4.5,
        right=4.5,
        height=13.5,
        lead_diameter=1.0,
        lead_length=4.1,
        opening_width_bottom=1.95,  # Measured in STEP model
        opening_width=4.0,  # Measured in STEP model
        opening_height=6.6,  # Guessed
        screw_hole_diameter=4.0,  # Measured in STEP model
        conductor_cross_section='2.5 mm²',
        walls_length=0.0,
        nipples_bottom=[
            Nipple(x=2.5, width=1.0, height=0.7),
        ],
        datasheet='https://www.phoenixcontact.com/us/products/{mpn}/pdf',
        keywords=[],
        draw_body_sketch_fn=lambda workplane: workplane.moveTo(4.5, 0.0)
        .lineTo(4.5, 13.5)
        .lineTo(-2.5, 13.5)
        .lineTo(-3.5, 6.5)
        .lineTo(-4.0, 6.5)
        .ellipseArc(x_radius=0.5, y_radius=0.5, angle1=90, angle2=180, sense=1)
        .lineTo(-4.5, 0.0),
    )
    models = [
        Model(name='PT 2,5/2-5,0-H', mpn='1935776', circuits=2),
        Model(name='PT 2,5/3-5,0-H', mpn='1935789', circuits=3),
        Model(name='PT 2,5/4-5,0-H', mpn='1935792', circuits=4),
        Model(name='PT 2,5/5-5,0-H', mpn='1935802', circuits=5),
        Model(name='PT 2,5/6-5,0-H', mpn='1935815', circuits=6),
        Model(name='PT 2,5/7-5,0-H', mpn='1935828', circuits=7),
        Model(name='PT 2,5/8-5,0-H', mpn='1935831', circuits=8),
        Model(name='PT 2,5/9-5,0-H', mpn='1935844', circuits=9),
        Model(name='PT 2,5/10-5,0-H', mpn='1935857', circuits=10),
        Model(name='PT 2,5/11-5,0-H', mpn='1935860', circuits=11),
        Model(name='PT 2,5/12-5,0-H', mpn='1935873', circuits=12),
        Model(name='PT 2,5/13-5,0-H', mpn='1935886', circuits=13),
        Model(name='PT 2,5/14-5,0-H', mpn='1935899', circuits=14),
        Model(name='PT 2,5/15-5,0-H', mpn='1935909', circuits=15),
        Model(name='PT 2,5/16-5,0-H', mpn='1935912', circuits=16),
    ]
    for model in models:
        generate_pkg(
            library='Phoenix.lplib',
            author='U. Bruhin',
            version='0.1',
            create_date='2025-04-10T13:33:42Z',
            family=family,
            model=model,
            generate_3d_models=generate_3d_models,
        )
        generate_dev(
            library='Phoenix.lplib',
            author='U. Bruhin',
            version='0.1',
            create_date='2025-04-10T13:33:42Z',
            family=family,
            model=model,
        )

    save_cache(uuid_cache_file, uuid_cache)
