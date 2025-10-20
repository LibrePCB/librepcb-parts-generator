"""
Generate THT rectangular capacitors.
"""

import sys
from os import path
from uuid import uuid4

from typing import Any, Optional

from common import format_ipc_dimension, init_cache, now, save_cache
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
)
from entities.component import SignalUUID
from entities.device import ComponentPad, ComponentUUID, Device, PackageUUID
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

generator = 'librepcb-parts-generator (generate_capacitor_rect_tht.py)'

# Lookup table to get the drill diameter from a given lead diameter.
LEAD_WIDTH_TO_DRILL = {
    0.4: 0.5,
    0.45: 0.6,
    0.5: 0.7,
    0.6: 0.8,
    0.8: 1.0,
}
RESTRING = 0.35
LINE_WIDTH = 0.2
COURTYARD_EXCESS = 0.4

# Initialize UUID cache
uuid_cache_file = 'uuid_cache_capacitors_rect_tht.csv'
uuid_cache = init_cache(uuid_cache_file)


def uuid(category: str, full_name: str, identifier: str) -> str:
    """
    Return a uuid for the specified element.

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


#def get_variant(
#    diameter: float,
#    height: float,
#    pitch: float,
#    lead_width: float,
#) -> str:
#    return 'D{}-H{}-P{}-W{}'.format(diameter, height, pitch, lead_width)


class Color:
    def __init__(self, identifier: str, name: str, cq_name: str):
        self.identifier = identifier
        self.name = name
        self.cq_name = cq_name

Color.RED = Color('rd', 'red', 'coral2')


class PackageConfig:
    def __init__(self, pitch: float, width: float, length: float, height: float, lead_diameter: float, lead_length: float, color: Color):
        self.pitch = pitch
        self.width = width
        self.length = length
        self.height = height
        self.lead_diameter = lead_diameter
        self.lead_length = lead_length
        self.color = color

    def get_identifier(self):
        return 'p{}-d{}-l{}-w{}-h{}-{}'.format(
            format_ipc_dimension(self.pitch),
            format_ipc_dimension(self.lead_diameter),
            format_ipc_dimension(self.length),
            format_ipc_dimension(self.width),
            format_ipc_dimension(self.height),
            self.color.identifier,
        )

    def get_name(self):
        # Name according IPC-7351 "Capacitor, Non Polarized Radial Rectangular":
        # CAPRR + Lead Spacing + W Lead Width + L Body Length + T Body Thickness + H Body Height
        return 'CAPRR{}W{}L{}T{}H{}-{}'.format(
            format_ipc_dimension(self.pitch),
            format_ipc_dimension(self.lead_diameter),
            format_ipc_dimension(self.length),
            format_ipc_dimension(self.width),
            format_ipc_dimension(self.height),
            self.color.name.upper(),
        )

    def get_description(self):
        return ''


def generate_pkg(
    library: str,
    config: PackageConfig,
    generate_3d_models: bool,
    author: str,
    version: str,
    create_date: Optional[str] = None,
) -> None:
    def _uuid(identifier: str) -> str:
        return uuid('pkg', config.get_identifier(), identifier)

    uuid_pkg = _uuid('pkg')

    print('Generating {}: {}'.format(config.get_name(), uuid_pkg))

    package = Package(
        uuid=uuid_pkg,
        name=Name(config.get_name()),
        description=Description(config.get_description()),
        keywords=Keywords(''),
        author=Author(author),
        version=Version(version),
        created=Created(create_date or now()),
        deprecated=Deprecated(False),
        generated_by=GeneratedBy(''),
        categories=[
            Category('414f873f-4099-47fd-8526-bdd8419de581')
        ],
        assembly_type=AssemblyType.THT,
    )

    # Package pads
    package.add_pad(PackagePad(uuid=_uuid('pad-1'), name=Name('1')))
    package.add_pad(PackagePad(uuid=_uuid('pad-2'), name=Name('2')))

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
    drill = LEAD_WIDTH_TO_DRILL[config.lead_diameter]
    pad_diameter = drill + (2 * RESTRING)  # outer diameter of pad
    for sign, name in [(-1, '1'), (1, '2')]:
        uuid_fpt_pad = _uuid(f'default-pad-{name}')
        footprint.add_pad(FootprintPad(
            uuid=uuid_fpt_pad,
            side=ComponentSide.TOP,
            shape=Shape.ROUNDED_RECT,
            position=Position(sign * (config.pitch / 2), 0),
            rotation=Rotation(0),
            size=Size(pad_diameter, pad_diameter),
            radius=ShapeRadius(1),
            stop_mask=StopMaskConfig(StopMaskConfig.AUTO),
            solder_paste=SolderPasteConfig.OFF,
            copper_clearance=CopperClearance(0),
            function=PadFunction.STANDARD_PAD,
            package_pad=PackagePadUuid(_uuid(f'pad-{name}')),
            holes=[PadHole(uuid_fpt_pad, DrillDiameter(drill),
                            [Vertex(Position(0.0, 0.0), Angle(0.0))])],
        ))

    # Documentation outline
    dx = (config.length / 2) - (LINE_WIDTH / 2)
    dy = (config.width / 2) - (LINE_WIDTH / 2)
    footprint.add_polygon(Polygon(
        uuid=_uuid('default-polygon-documentation'),
        layer=Layer('top_documentation'),
        width=Width(LINE_WIDTH),
        fill=Fill(False),
        grab_area=GrabArea(False),
        vertices=[
            Vertex(Position(-dx, dy), Angle(0)),
            Vertex(Position(dx, dy), Angle(0)),
            Vertex(Position(dx, -dy), Angle(0)),
            Vertex(Position(-dx, -dy), Angle(0)),
            Vertex(Position(-dx, dy), Angle(0)),
        ],
    ))

    # Legend outline
    dx = (config.length / 2) + (LINE_WIDTH / 2)
    dy = (config.width / 2) + (LINE_WIDTH / 2)
    footprint.add_polygon(Polygon(
        uuid=_uuid('default-polygon-legend'),
        layer=Layer('top_legend'),
        width=Width(LINE_WIDTH),
        fill=Fill(False),
        grab_area=GrabArea(False),
        vertices=[
            Vertex(Position(-dx, dy), Angle(0)),
            Vertex(Position(dx, dy), Angle(0)),
            Vertex(Position(dx, -dy), Angle(0)),
            Vertex(Position(-dx, -dy), Angle(0)),
            Vertex(Position(-dx, dy), Angle(0)),
        ],
    ))

    # Package outline
    dx = config.length / 2
    dy = config.width / 2
    footprint.add_polygon(Polygon(
        uuid=_uuid('default-polygon-outline'),
        layer=Layer('top_package_outlines'),
        width=Width(0),
        fill=Fill(False),
        grab_area=GrabArea(False),
        vertices=[
            Vertex(Position(-dx, dy), Angle(0)),
            Vertex(Position(dx, dy), Angle(0)),
            Vertex(Position(dx, -dy), Angle(0)),
            Vertex(Position(-dx, -dy), Angle(0)),
        ],
    ))

    # Courtyard
    dx += COURTYARD_EXCESS
    dy += COURTYARD_EXCESS
    footprint.add_polygon(Polygon(
        uuid=_uuid('default-polygon-courtyard'),
        layer=Layer('top_courtyard'),
        width=Width(0),
        fill=Fill(False),
        grab_area=GrabArea(False),
        vertices=[
            Vertex(Position(-dx, dy), Angle(0)),
            Vertex(Position(dx, dy), Angle(0)),
            Vertex(Position(dx, -dy), Angle(0)),
            Vertex(Position(-dx, -dy), Angle(0)),
        ],
    ))

    # Labels
    top = (config.width / 2) + LINE_WIDTH
    bottom = -top
    footprint.add_text(StrokeText(
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
    ))
    footprint.add_text(StrokeText(
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
    ))

    # Generate 3D model
    uuid_3d = _uuid('3d')
    if generate_3d_models:
        generate_3d(library, uuid_pkg, uuid_3d, config)
    package.add_3d_model(Package3DModel(uuid_3d, Name(config.get_name())))
    for footprint in package.footprints:
        footprint.add_3d_model(Footprint3DModel(uuid_3d))

    package.serialize(path.join('out', library, 'pkg'))


def generate_3d(
    library: str,
    uuid_pkg: str,
    uuid_3d: str,
    config: PackageConfig,
) -> None:
    import cadquery as cq

    from cadquery_helpers import StepAssembly, StepColor, StepConstants

    print(f'Generating pkg 3D model "{config.get_name()}": {uuid_3d}')

    body_fillet = 0.2

    body = cq.Workplane('XY', origin=(0, 0, 0)).box(
        config.length, config.width, config.height, centered=(True, True, False)
    ).edges("|Z or >Z").fillet(body_fillet)
    leg = cq.Workplane('XY', origin=(0, 0, -config.lead_length)).cylinder(config.lead_length + 1, config.lead_diameter / 2, centered=(True, True, False))

    assembly = StepAssembly(config.get_name())
    assembly.add_body(body, 'body', cq.Color(config.color.cq_name))
    assembly.add_body(leg, 'leg-1', StepColor.LEAD_THT, location=cq.Location((-config.pitch / 2, 0, 0)))
    assembly.add_body(leg, 'leg-2', StepColor.LEAD_THT, location=cq.Location((config.pitch / 2, 0, 0)))

    # Save with fusing since there are not many reused assembly parts.
    out_path = path.join('out', library, 'pkg', uuid_pkg, f'{uuid_3d}.step')
    assembly.save(out_path, fused=True)


#def generate_dev(
#    library: str,
#    diameter: float,
#    height: float,
#    pitch: float,
#    lead_width: float,
#    author: str,
#    version: str,
#    create_date: Optional[str],
#) -> None:
#    name = 'Capacitor Radial ⌀{}x{}/{}mm'.format(diameter, height, pitch)
#    variant = get_variant(diameter, height, pitch, lead_width)
#
#    def _uuid(identifier: str) -> str:
#        return uuid('dev', variant, identifier)
#
#    device = Device(
#        uuid=_uuid('dev'),
#        name=Name(name),
#        description=Description(
#            'Generic polarized radial electrolytic capacitor.\n\n'
#            + 'Diameter: {} mm\n'.format(diameter)
#            + 'Height: {} mm\n'.format(height)
#            + 'Lead Spacing: {} mm\n'.format(pitch)
#            + 'Max. Lead Diameter: {} mm\n\n'.format(lead_width)
#            + 'Generated with {}'.format(generator)
#        ),
#        keywords=Keywords('electrolytic,capacitor,polarized,radial,c,cap,cpol'),
#        author=Author(author),
#        version=Version(version),
#        created=Created(create_date or now()),
#        deprecated=Deprecated(False),
#        generated_by=GeneratedBy(''),
#        categories=[Category('c011cc6b-b762-498e-8494-d1994f3043cf')],
#        component_uuid=ComponentUUID('c54375c5-7149-4ded-95c5-7462f7301ee7'),
#        package_uuid=PackageUUID(uuid('pkg', variant, 'pkg')),
#    )
#    device.add_pad(
#        ComponentPad(
#            pad_uuid=uuid('pkg', variant, 'pad-plus'),
#            signal=SignalUUID('e010ecbb-6210-4da3-9270-ebd58656dbf0'),
#        )
#    )
#    device.add_pad(
#        ComponentPad(
#            pad_uuid=uuid('pkg', variant, 'pad-minus'),
#            signal=SignalUUID('af3ffca8-0085-4edb-a775-fcb759f63411'),
#        )
#    )
#
#    # write files
#    device.serialize(path.join('out', library, 'dev'))
#    print('Wrote device {}'.format(name))


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


    configs = [
        # Pitch 2.5mm
        PackageConfig(
            pitch=2.5,
            width=2.5,
            length=4.6,
            height=7.0,
            lead_diameter=0.4,
            lead_length=6.0,
            color=Color.RED,
        ),
        PackageConfig(
            pitch=2.5,
            width=3.0,
            length=4.6,
            height=7.5,
            lead_diameter=0.4,
            lead_length=6.0,
            color=Color.RED,
        ),
        PackageConfig(
            pitch=2.5,
            width=3.8,
            length=4.6,
            height=8.5,
            lead_diameter=0.4,
            lead_length=6.0,
            color=Color.RED,
        ),
        PackageConfig(
            pitch=2.5,
            width=4.6,
            length=4.6,
            height=9.0,
            lead_diameter=0.4,
            lead_length=6.0,
            color=Color.RED,
        ),
        PackageConfig(
            pitch=2.5,
            width=5.5,
            length=4.6,
            height=10.0,
            lead_diameter=0.4,
            lead_length=6.0,
            color=Color.RED,
        ),
    ]

    for config in configs:
        generate_pkg(
            library='LibrePCB_Base.lplib',
            config=config,
            generate_3d_models=generate_3d_models,
            author='U. Bruhin',
            version='0.1',
            create_date='2025-10-17T13:49:55Z',
        )
        #generate_dev(
        #    library='LibrePCB_Base.lplib',
        #    diameter=config['diameter'],
        #    height=config['height'],
        #    pitch=config['pitch'],
        #    lead_width=config['lead_width'],
        #    author='U. Bruhin',
        #    version='0.1',
        #    create_date='2019-12-29T14:14:11Z',
        #)

    save_cache(uuid_cache_file, uuid_cache)
