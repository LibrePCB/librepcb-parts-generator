"""
Generate THT polarized radial electrolytic capacitors (CAPPRD).
"""
import sys
from os import path
from uuid import uuid4

from typing import Any, Optional

from common import format_ipc_dimension, init_cache, now, save_cache
from entities.common import (
    Align, Angle, Author, Category, Circle, Created, Deprecated, Description, Diameter, Fill, GeneratedBy, GrabArea,
    Height, Keywords, Layer, Name, Polygon, Position, Position3D, Rotation, Rotation3D, Value, Version, Vertex, Width
)
from entities.component import SignalUUID
from entities.device import ComponentPad, ComponentUUID, Device, PackageUUID
from entities.package import (
    AssemblyType, AutoRotate, ComponentSide, CopperClearance, DrillDiameter, Footprint, Footprint3DModel, FootprintPad,
    LetterSpacing, LineSpacing, Mirror, Package, Package3DModel, PackagePad, PackagePadUuid, PadFunction, PadHole,
    Shape, ShapeRadius, Size, SolderPasteConfig, StopMaskConfig, StrokeText, StrokeWidth
)

generator = 'librepcb-parts-generator (generate_capacitor_radial_tht.py)'

# Lookup table to get the drill diameter from a given lead diameter.
LEAD_WIDTH_TO_DRILL = {
    0.4: 0.5,
    0.45: 0.6,
    0.5: 0.7,
    0.6: 0.8,
    0.8: 1.0,
}

# Initialize UUID cache
uuid_cache_file = 'uuid_cache_capacitors_radial_tht.csv'
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


def get_variant(
    diameter: float,
    height: float,
    pitch: float,
    lead_width: float,
) -> str:
    return 'D{}-H{}-P{}-W{}'.format(diameter, height, pitch, lead_width)


def generate_pkg(
    library: str,
    diameter: float,
    height: float,
    pitch: float,
    lead_width: float,
    generate_3d_models: bool,
    author: str,
    version: str,
    create_date: Optional[str],
) -> None:
    # Name according IPC-7351 "Capacitor, Polarized Radial Diameter":
    # CAPPRD + Lead Spacing + W Lead Width + D Body Diameter + H Body Height
    name = 'CAPPRD{}W{}D{}H{}'.format(
        format_ipc_dimension(pitch), format_ipc_dimension(lead_width),
        format_ipc_dimension(diameter), format_ipc_dimension(height))
    variant = get_variant(diameter, height, pitch, lead_width)

    def _pkg_uuid(identifier: str) -> str:
        return uuid('pkg', variant, identifier)

    def _create_footprint(footprint_identifier: str, name: str) -> Footprint:

        def _fpt_uuid(identifier: str) -> str:
            return _pkg_uuid(footprint_identifier + '-' + identifier)

        drill = LEAD_WIDTH_TO_DRILL[lead_width]
        restring = min((0.4 if diameter >= 6.0 else 0.3),  # preferred restring
                       (pitch - drill - 0.25) / 2)  # minimum required restring
        pad_diameter = drill + (2 * restring)  # outer diameter of pad
        courtyard_diameter = diameter + (1.0 if diameter >= 10.0 else 0.8)

        def _generate_fill_polygon(identifier: str, layer: str) -> Polygon:
            polygon = Polygon(
                uuid=_fpt_uuid(identifier),
                layer=Layer(layer),
                width=Width(0.0),
                fill=Fill(True),
                grab_area=GrabArea(False),
            )
            if ((pitch - pad_diameter) < 0.6):
                # not enough space, use a simplified polygon
                vertices = [
                    (0.0, (diameter / 2) - 0.2, 0.0),
                    (0.0, (pad_diameter / 2) + 0.2, 0.0),
                    (pitch / 2, (pad_diameter / 2) + 0.2, -180.0),
                    (pitch / 2, -(pad_diameter / 2) - 0.2, 0.0),
                    (0.0, -(pad_diameter / 2) - 0.2, 0.0),
                    (0.0, -(diameter / 2) + 0.2, 180.0),
                    (0.0, (diameter / 2) - 0.2, 0.0),
                ]
            else:
                vertices = [
                    (0.0, (diameter / 2) - 0.2, 0.0),
                    (0.0, 0.0, 0.0),
                    ((pitch / 2) - (pad_diameter / 2) - 0.2, 0.0, -180.0),
                    ((pitch / 2) + (pad_diameter / 2) + 0.2, 0.0, -180.0),
                    ((pitch / 2) - (pad_diameter / 2) - 0.2, 0.0, 0.0),
                    (0.0, 0.0, 0.0),
                    (0.0, -(diameter / 2) + 0.2, 180.0),
                    (0.0, (diameter / 2) - 0.2, 0.0),
                ]
            for vertex in vertices:
                polygon.add_vertex(Vertex(Position(vertex[0], vertex[1]), Angle(vertex[2])))
            return polygon

        footprint = Footprint(
            uuid=_fpt_uuid('footprint'),
            name=Name(name),
            description=Description(''),
            position_3d=Position3D.zero(),
            rotation_3d=Rotation3D.zero(),
        )
        pad_hole_path = [Vertex(Position(0.0, 0.0), Angle(0.0))]
        uuid_plus = _pkg_uuid('pad-plus')
        footprint.add_pad(FootprintPad(
            uuid=uuid_plus,
            side=ComponentSide.TOP,
            shape=Shape.ROUNDED_RECT,
            position=Position(-pitch / 2, 0),
            rotation=Rotation(0),
            size=Size(pad_diameter, pad_diameter),
            radius=ShapeRadius(0.0),
            stop_mask=StopMaskConfig.AUTO,
            solder_paste=SolderPasteConfig.OFF,
            copper_clearance=CopperClearance(0),
            function=PadFunction.STANDARD_PAD,
            package_pad=PackagePadUuid(uuid_plus),
            holes=[PadHole(uuid_plus, DrillDiameter(drill), pad_hole_path)],
        ))
        uuid_minus = _pkg_uuid('pad-minus')
        footprint.add_pad(FootprintPad(
            uuid=uuid_minus,
            side=ComponentSide.TOP,
            shape=Shape.ROUNDED_RECT,
            position=Position(pitch / 2, 0),
            rotation=Rotation(0),
            size=Size(pad_diameter, pad_diameter),
            radius=ShapeRadius(1.0),
            stop_mask=StopMaskConfig.AUTO,
            solder_paste=SolderPasteConfig.OFF,
            copper_clearance=CopperClearance(0),
            function=PadFunction.STANDARD_PAD,
            package_pad=PackagePadUuid(uuid_minus),
            holes=[PadHole(uuid_minus, DrillDiameter(drill), pad_hole_path)],
        ))

        # placement
        footprint.add_circle(Circle(
            uuid=_fpt_uuid('circle-placement'),
            layer=Layer('top_legend'),
            width=Width(0.2),
            fill=Fill(False),
            grab_area=GrabArea(False),
            diameter=Diameter(diameter + 0.2),
            position=Position(0.0, 0.0),
        ))
        footprint.add_polygon(_generate_fill_polygon(
            identifier='polygon-placement-fill',
            layer='top_legend',
        ))

        # documentation
        footprint.add_circle(Circle(
            uuid=_fpt_uuid('circle-documentation'),
            layer=Layer('top_documentation'),
            width=Width(0.2),
            fill=Fill(False),
            grab_area=GrabArea(False),
            diameter=Diameter(diameter - 0.2),
            position=Position(0.0, 0.0),
        ))
        footprint.add_polygon(_generate_fill_polygon(
            identifier='polygon-documentation-fill',
            layer='top_documentation',
        ))

        # package outline
        footprint.add_circle(Circle(
            uuid=_fpt_uuid('circle-outline'),
            layer=Layer('top_package_outlines'),
            width=Width(0.0),
            fill=Fill(False),
            grab_area=GrabArea(False),
            diameter=Diameter(diameter),
            position=Position(0.0, 0.0),
        ))

        # courtyard
        footprint.add_circle(Circle(
            uuid=_fpt_uuid('circle-courtyard'),
            layer=Layer('top_courtyard'),
            width=Width(0.0),
            fill=Fill(False),
            grab_area=GrabArea(False),
            diameter=Diameter(courtyard_diameter),
            position=Position(0.0, 0.0),
        ))

        # texts
        footprint.add_text(StrokeText(
            uuid=_fpt_uuid('text-name'),
            layer=Layer('top_names'),
            height=Height(1.0),
            stroke_width=StrokeWidth(0.2),
            letter_spacing=LetterSpacing.AUTO,
            line_spacing=LineSpacing.AUTO,
            align=Align('center bottom'),
            position=Position(0.0, (diameter / 2) + 0.8),
            rotation=Rotation(0.0),
            auto_rotate=AutoRotate(True),
            mirror=Mirror(False),
            value=Value('{{NAME}}'),
        ))
        footprint.add_text(StrokeText(
            uuid=_fpt_uuid('text-value'),
            layer=Layer('top_values'),
            height=Height(1.0),
            stroke_width=StrokeWidth(0.2),
            letter_spacing=LetterSpacing.AUTO,
            line_spacing=LineSpacing.AUTO,
            align=Align('center top'),
            position=Position(0.0, -(diameter / 2) - 0.8),
            rotation=Rotation(0.0),
            auto_rotate=AutoRotate(True),
            mirror=Mirror(False),
            value=Value('{{VALUE}}'),
        ))
        return footprint

    # package
    uuid_pkg = _pkg_uuid('pkg')
    package = Package(
        uuid=uuid_pkg,
        name=Name(name),
        description=Description(
            'Polarized radial electrolytic capacitor.\n\n' +
            'Diameter: {} mm\n'.format(diameter) +
            'Height: {} mm\n'.format(height) +
            'Lead Spacing: {} mm\n'.format(pitch) +
            'Max. Lead Diameter: {} mm\n\n'.format(lead_width) +
            'Generated with {}'.format(generator)
        ),
        keywords=Keywords('electrolytic,capacitor,polarized,radial,c,cap,cpol'),
        author=Author(author),
        version=Version(version),
        created=Created(create_date or now()),
        deprecated=Deprecated(False),
        generated_by=GeneratedBy(''),
        categories=[Category('ee75e31d-f231-41d9-8a3b-bea5114f41e3')],
        assembly_type=AssemblyType.THT,
    )
    package.add_pad(PackagePad(uuid=_pkg_uuid('pad-plus'), name=Name('+')))
    package.add_pad(PackagePad(uuid=_pkg_uuid('pad-minus'), name=Name('-')))
    package.add_footprint(_create_footprint(
        footprint_identifier='default',
        name='default',
    ))

    # Generate 3D models
    uuid_3d = _pkg_uuid('3d')
    if generate_3d_models:
        generate_3d(library, name, uuid_pkg, uuid_3d, diameter, height,
                    pitch, lead_width)
    package.add_3d_model(Package3DModel(uuid_3d, Name(name)))
    for footprint in package.footprints:
        footprint.add_3d_model(Footprint3DModel(uuid_3d))

    # write files
    package.serialize(path.join('out', library, 'pkg'))
    print('Wrote package {}'.format(name))


def generate_3d(
    library: str,
    name: str,
    uuid_pkg: str,
    uuid_3d: str,
    diameter: float,
    height: float,
    pitch: float,
    lead_width: float,
) -> None:
    import cadquery as cq

    from cadquery_helpers import StepAssembly, StepColor, StepConstants

    print(f'Generating pkg 3D model "{name}": {uuid_3d}')

    body_fillet = min(diameter * 0.1, 1.0)
    body_ring_radius = min(diameter * 0.05, 1.0)
    body_ring_circle_radius = (diameter / 2) + (body_ring_radius / 2)
    body_ring_z = body_fillet + body_ring_radius * 3
    marking_angle = 40
    core_radius = diameter * 0.35
    core_depth = min(diameter * 0.02, 0.5)

    body_ring_cutout = cq.Workplane('XZ', origin=(-body_ring_circle_radius, 0, body_ring_z)) \
        .circle(body_ring_radius) \
        .revolve(360, (body_ring_circle_radius, 0, 0), (body_ring_circle_radius, -1, 0))

    def _make_body(start_angle: float, angle: float) -> Any:
        return cq.Workplane("XZ") \
            .transformed(rotate=(0, -start_angle, 0)) \
            .transformed(offset=(core_radius, 0, 0)) \
            .hLine((diameter / 2) - core_radius - body_fillet) \
            .ellipseArc(x_radius=body_fillet, y_radius=body_fillet, angle1=270, angle2=360, sense=1) \
            .vLine(height - (2 * body_fillet)) \
            .ellipseArc(x_radius=body_fillet, y_radius=body_fillet, angle1=360, angle2=90, sense=1) \
            .hLine(-(diameter / 2) + core_radius + body_fillet) \
            .close() \
            .revolve(angle, (-core_radius, 0, 0), (-core_radius, -1, 0)) \
            .cut(body_ring_cutout)

    body = _make_body(marking_angle / 2, 360 - marking_angle)
    marking = _make_body(-marking_angle / 2, marking_angle)
    core = cq.Workplane('XY', origin=(0, 0, core_depth)) \
        .cylinder(height - 2 * core_depth, core_radius, centered=(True, True, False))
    leg = cq.Workplane("XY").workplane(offset=(-core_depth - 1), invert=True) \
        .cylinder(StepConstants.THT_LEAD_SOLDER_LENGTH + core_depth + 1, lead_width / 2,
                  centered=(True, True, False))

    assembly = StepAssembly(name)
    assembly.add_body(body, 'body', cq.Color('gray16'))
    assembly.add_body(marking, 'marking', cq.Color('gray60'))
    assembly.add_body(core, 'core', cq.Color('ghostwhite'))
    assembly.add_body(leg, 'leg-1', StepColor.LEAD_THT,
                      location=cq.Location((-pitch / 2, 0, 0)))
    assembly.add_body(leg, 'leg-2', StepColor.LEAD_THT,
                      location=cq.Location((pitch / 2, 0, 0)))

    # Save with fusing since there are not many reused assembly parts.
    out_path = path.join('out', library, 'pkg', uuid_pkg, f'{uuid_3d}.step')
    assembly.save(out_path, fused=True)


def generate_dev(
    library: str,
    diameter: float,
    height: float,
    pitch: float,
    lead_width: float,
    author: str,
    version: str,
    create_date: Optional[str],
) -> None:
    name = 'Capacitor Radial ⌀{}x{}/{}mm'.format(diameter, height, pitch)
    variant = get_variant(diameter, height, pitch, lead_width)

    def _uuid(identifier: str) -> str:
        return uuid('dev', variant, identifier)

    device = Device(
        uuid=_uuid('dev'),
        name=Name(name),
        description=Description(
            'Generic polarized radial electrolytic capacitor.\n\n' +
            'Diameter: {} mm\n'.format(diameter) +
            'Height: {} mm\n'.format(height) +
            'Lead Spacing: {} mm\n'.format(pitch) +
            'Max. Lead Diameter: {} mm\n\n'.format(lead_width) +
            'Generated with {}'.format(generator)
        ),
        keywords=Keywords('electrolytic,capacitor,polarized,radial,c,cap,cpol'),
        author=Author(author),
        version=Version(version),
        created=Created(create_date or now()),
        deprecated=Deprecated(False),
        generated_by=GeneratedBy(''),
        categories=[Category('c011cc6b-b762-498e-8494-d1994f3043cf')],
        component_uuid=ComponentUUID('c54375c5-7149-4ded-95c5-7462f7301ee7'),
        package_uuid=PackageUUID(uuid('pkg', variant, 'pkg')),
    )
    device.add_pad(ComponentPad(
        pad_uuid=uuid('pkg', variant, 'pad-plus'),
        signal=SignalUUID('e010ecbb-6210-4da3-9270-ebd58656dbf0'),
    ))
    device.add_pad(ComponentPad(
        pad_uuid=uuid('pkg', variant, 'pad-minus'),
        signal=SignalUUID('af3ffca8-0085-4edb-a775-fcb759f63411'),
    ))

    # write files
    device.serialize(path.join('out', library, 'dev'))
    print('Wrote device {}'.format(name))


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

    CONFIGS = [
        # Some typical, frequently used configurations. The lead width depends
        # from package to package, thus choosing the highest value to ensure
        # compatibility with all variants (models with thinner leads can
        # still be mount).
        {'diameter':  3.0, 'height':  5.0, 'pitch': 1.0, 'lead_width': 0.4},
        {'diameter':  4.0, 'height':  5.0, 'pitch': 1.5, 'lead_width': 0.45},
        {'diameter':  4.0, 'height':  7.0, 'pitch': 1.5, 'lead_width': 0.45},
        {'diameter':  4.0, 'height': 11.0, 'pitch': 1.5, 'lead_width': 0.45},
        {'diameter':  5.0, 'height':  5.0, 'pitch': 2.0, 'lead_width': 0.5},
        {'diameter':  5.0, 'height':  7.0, 'pitch': 2.0, 'lead_width': 0.5},
        {'diameter':  5.0, 'height': 11.0, 'pitch': 2.0, 'lead_width': 0.5},
        {'diameter':  6.3, 'height':  5.0, 'pitch': 2.5, 'lead_width': 0.5},
        {'diameter':  6.3, 'height':  7.0, 'pitch': 2.5, 'lead_width': 0.5},
        {'diameter':  6.3, 'height': 11.0, 'pitch': 2.5, 'lead_width': 0.5},
        {'diameter':  8.0, 'height':  5.0, 'pitch': 2.5, 'lead_width': 0.6},
        {'diameter':  8.0, 'height':  7.0, 'pitch': 3.5, 'lead_width': 0.6},
        {'diameter':  8.0, 'height': 11.5, 'pitch': 3.5, 'lead_width': 0.6},
        {'diameter': 10.0, 'height': 12.5, 'pitch': 5.0, 'lead_width': 0.6},
        {'diameter': 10.0, 'height': 16.0, 'pitch': 5.0, 'lead_width': 0.6},
        {'diameter': 10.0, 'height': 20.0, 'pitch': 5.0, 'lead_width': 0.6},
        {'diameter': 12.5, 'height': 20.0, 'pitch': 5.0, 'lead_width': 0.8},
        {'diameter': 12.5, 'height': 25.0, 'pitch': 5.0, 'lead_width': 0.8},
        {'diameter': 16.0, 'height': 25.0, 'pitch': 7.5, 'lead_width': 0.8},
        {'diameter': 16.0, 'height': 31.5, 'pitch': 7.5, 'lead_width': 0.8},
        {'diameter': 18.0, 'height': 35.5, 'pitch': 7.5, 'lead_width': 0.8},
    ]

    for config in CONFIGS:
        generate_pkg(
            library='LibrePCB_Base.lplib',
            diameter=config['diameter'],
            height=config['height'],
            pitch=config['pitch'],
            lead_width=config['lead_width'],
            generate_3d_models=generate_3d_models,
            author='U. Bruhin',
            version='0.2',
            create_date='2019-12-29T14:14:11Z',
        )
        generate_dev(
            library='LibrePCB_Base.lplib',
            diameter=config['diameter'],
            height=config['height'],
            pitch=config['pitch'],
            lead_width=config['lead_width'],
            author='U. Bruhin',
            version='0.1',
            create_date='2019-12-29T14:14:11Z',
        )

    save_cache(uuid_cache_file, uuid_cache)
