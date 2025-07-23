"""
Generate mounting hole packages & devices

- ISO4762: https://cdn.standards.iteh.ai/samples/34460/06335046afaf46fb8e84d91a3eda001d/ISO-4762-2004.pdf
- ISO7380: https://cdn.standards.iteh.ai/samples/78699/a175805085534f98983d6c8aa583a5b0/ISO-7380-1-2022.pdf
- ISO14580: https://cdn.standards.iteh.ai/samples/56456/88025f720d57423b9e2c1ceb78304eec/ISO-14580-2011.pdf
- DIN965: https://www.aramfix.com/content/files/d965cagll/datasheet%20din%20965.pdf
"""

from os import path
from uuid import uuid4

from typing import Optional

from common import init_cache, now, save_cache
from entities.common import (
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
    Keywords,
    Layer,
    Name,
    Position,
    Position3D,
    Rotation,
    Rotation3D,
    Version,
    Vertex,
    Width,
)
from entities.component import SignalUUID
from entities.device import ComponentPad, ComponentUUID, Device, PackageUUID
from entities.package import (
    AssemblyType,
    ComponentSide,
    CopperClearance,
    DrillDiameter,
    Footprint,
    FootprintPad,
    Hole,
    Package,
    PackagePad,
    PackagePadUuid,
    PadFunction,
    PadHole,
    Shape,
    ShapeRadius,
    Size,
    SolderPasteConfig,
    StopMaskConfig,
    Zone,
)

generator = 'librepcb-parts-generator (generate_mounting_holes.py)'

line_width = 0.2
legend_clearance = 0.1
copper_clearance = 0.2
stopmask_excess = 0.05
courtyard_excess = 0.5


# Initialize UUID cache
uuid_cache_file = 'uuid_cache_mounting_holes.csv'
uuid_cache = init_cache(uuid_cache_file)


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
    name: str,
    hole_diameter: float,
    pad_diameter: float,
) -> None:
    full_name = f'MOUNTING_HOLE_{name}'
    full_desc = f"""Generic mounting hole for {name} screws, compatible with ISO7380, ISO14580 and DIN965.

Hole diameter: {hole_diameter:.2f} mm
Pad diameter: {pad_diameter:.2f} mm

Generated with {generator}
"""
    keywords = f'mounting,hole,pad,drill,screw,{name},{hole_diameter}mm,{pad_diameter}mm'

    def _uuid(identifier: str) -> str:
        return uuid('pkg', name.lower(), identifier)

    uuid_pkg = _uuid('pkg')

    print('Generating {}: {}'.format(full_name, uuid_pkg))

    package = Package(
        uuid=uuid_pkg,
        name=Name(full_name),
        description=Description(full_desc),
        keywords=Keywords(keywords),
        author=Author(author),
        version=Version(version),
        created=Created(create_date or now()),
        deprecated=Deprecated(False),
        generated_by=GeneratedBy(''),
        categories=[Category('1d2630f1-c375-49f0-a0dc-2446735d82f4')],
        assembly_type=AssemblyType.NONE,
    )

    uuid_pkg_pad = _uuid('pad')
    package.add_pad(PackagePad(uuid=uuid_pkg_pad, name=Name('1')))

    def _add_footprint(name: str, pad: bool, cover: bool) -> None:
        uuid_ns = name + '-'
        footprint = Footprint(
            uuid=_uuid(uuid_ns + 'footprint'),
            name=Name(name),
            description=Description(''),
            position_3d=Position3D.zero(),
            rotation_3d=Rotation3D.zero(),
        )
        package.add_footprint(footprint)

        # Pad or hole
        if pad:
            uuid_pad = _uuid(uuid_ns + 'pad')
            footprint.add_pad(
                FootprintPad(
                    uuid=uuid_pad,
                    side=ComponentSide.TOP,
                    shape=Shape.ROUNDED_RECT,
                    position=Position(0, 0),
                    rotation=Rotation(0),
                    size=Size(pad_diameter, pad_diameter),
                    radius=ShapeRadius(1),
                    stop_mask=StopMaskConfig(stopmask_excess),
                    solder_paste=SolderPasteConfig.OFF,
                    copper_clearance=CopperClearance(copper_clearance),
                    function=PadFunction.STANDARD_PAD,
                    package_pad=PackagePadUuid(uuid_pkg_pad),
                    holes=[
                        PadHole(
                            uuid_pad,
                            DrillDiameter(hole_diameter),
                            [Vertex(Position(0.0, 0.0), Angle(0.0))],
                        )
                    ],
                )
            )
            package.add_approval(
                '(approved pad_with_copper_clearance\n'
                + ' (footprint {})\n'.format(footprint.uuid)
                + ' (pad {})\n'.format(uuid_pad)
                + ')'
            )
        else:
            footprint.add_hole(
                Hole(
                    uuid=_uuid(uuid_ns + 'hole'),
                    diameter=DrillDiameter(hole_diameter),
                    vertices=[Vertex(Position(0.0, 0.0), Angle(0.0))],
                    stop_mask=StopMaskConfig(StopMaskConfig.AUTO),
                )
            )
            zone_y = (pad_diameter / 2) + copper_clearance
            footprint.add_zone(
                Zone(
                    uuid=_uuid(uuid_ns + 'zone'),
                    top=True,
                    inner=False,
                    bottom=True,
                    no_copper=True,
                    no_planes=True,
                    no_exposure=cover,
                    no_devices=False,
                    vertices=[
                        Vertex(Position(0.0, zone_y), Angle(180.0)),
                        Vertex(Position(0.0, -zone_y), Angle(180.0)),
                        Vertex(Position(0.0, zone_y), Angle(0.0)),
                    ],
                )
            )

        for side in ['top', 'bot']:
            # Stop mask
            if not pad and not cover:
                footprint.add_circle(
                    Circle(
                        uuid=_uuid(uuid_ns + 'circle-stopmask-' + side),
                        layer=Layer(side + '_stop_mask'),
                        width=Width(0),
                        fill=Fill(True),
                        grab_area=GrabArea(False),
                        diameter=Diameter(pad_diameter + 2 * stopmask_excess),
                        position=Position(0, 0),
                    )
                )

            # Documentation
            footprint.add_circle(
                Circle(
                    uuid=_uuid(uuid_ns + 'circle-documentation-' + side),
                    layer=Layer(side + '_documentation'),
                    width=Width(line_width),
                    fill=Fill(False),
                    grab_area=GrabArea(True),
                    diameter=Diameter(pad_diameter + line_width + 2 * legend_clearance),
                    position=Position(0, 0),
                )
            )

            # Legend
            footprint.add_circle(
                Circle(
                    uuid=_uuid(uuid_ns + 'circle-legend-' + side),
                    layer=Layer(side + '_legend'),
                    width=Width(line_width),
                    fill=Fill(False),
                    grab_area=GrabArea(True),
                    diameter=Diameter(pad_diameter + line_width + 2 * legend_clearance),
                    position=Position(0, 0),
                )
            )

            # Package outline
            footprint.add_circle(
                Circle(
                    uuid=_uuid(uuid_ns + 'circle-outline-' + side),
                    layer=Layer(side + '_package_outlines'),
                    width=Width(0),
                    fill=Fill(False),
                    grab_area=GrabArea(False),
                    diameter=Diameter(pad_diameter + 2 * legend_clearance),
                    position=Position(0, 0),
                )
            )

            # Courtyard
            footprint.add_circle(
                Circle(
                    uuid=_uuid(uuid_ns + 'circle-courtyard-' + side),
                    layer=Layer(side + '_courtyard'),
                    width=Width(0),
                    fill=Fill(False),
                    grab_area=GrabArea(False),
                    diameter=Diameter(pad_diameter + 2 * courtyard_excess),
                    position=Position(0, 0),
                )
            )

        # Approvals
        package.add_approval(
            '(approved missing_name_text\n' + ' (footprint {})\n'.format(footprint.uuid) + ')'
        )
        package.add_approval(
            '(approved missing_value_text\n' + ' (footprint {})\n'.format(footprint.uuid) + ')'
        )

    _add_footprint('copper', pad=True, cover=False)
    _add_footprint('covered', pad=False, cover=True)
    _add_footprint('blank', pad=False, cover=False)

    package.add_approval('(approved suspicious_assembly_type)')

    package.serialize(path.join('out', library, 'pkg'))


def generate_dev(
    library: str,
    author: str,
    version: str,
    create_date: Optional[str],
    name: str,
    hole_diameter: float,
    pad_diameter: float,
) -> None:
    full_name = f'Mounting Hole {name}'
    full_desc = f"""Generic mounting hole for {name} screws, compatible with ISO7380, ISO14580 and DIN965.

Hole diameter: {hole_diameter:.2f} mm
Pad diameter: {pad_diameter:.2f} mm

Generated with {generator}
"""
    keywords = f'mounting,hole,pad,drill,screw,{name},{hole_diameter}mm,{pad_diameter}mm'

    def _uuid(identifier: str) -> str:
        return uuid('dev', name.lower(), identifier)

    uuid_dev = _uuid('dev')

    print('Generating {}: {}'.format(full_name, uuid_dev))

    device = Device(
        uuid=uuid_dev,
        name=Name(full_name),
        description=Description(full_desc),
        keywords=Keywords(keywords),
        author=Author(author),
        version=Version(version),
        created=Created(create_date or now()),
        deprecated=Deprecated(False),
        generated_by=GeneratedBy(''),
        categories=[
            Category('213bd44f-f375-41d8-8fdd-0652eb893e27'),
            Category('8ca4f9fb-3dd3-4c1e-a097-6601b437bbc6'),
        ],
        component_uuid=ComponentUUID('5c0f6cd9-dced-46ae-8098-6cccaa8726ec'),
        package_uuid=PackageUUID(uuid('pkg', name.lower(), 'pkg')),
    )

    device.add_pad(
        ComponentPad(
            uuid('pkg', name.lower(), 'pad'), SignalUUID('c8721bab-6c90-43f6-8135-c32fce7aecc0')
        )
    )
    device.add_approval('(approved no_parts)')

    device.serialize(path.join('out', library, 'dev'))


if __name__ == '__main__':
    # Maximum head diameters of standard screws:
    #
    # | Screw | ISO4762 | ISO7380 | ISO14580 | DIN965 |
    # |-------|---------|---------|----------|--------|
    # | M2    |     3.8 |         |      3.8 |    3.8 |
    # | M2.5  |     4.5 |         |      4.5 |    4.7 |
    # | M3    |     5.5 |     5.7 |      5.5 |    5.6 |
    # | M4    |     7.0 |     7.6 |      7.0 |    7.5 |
    # | M5    |     8.5 |     9.5 |      8.5 |    9.2 |
    # | M6    |    10.0 |    10.5 |     10.0 |   11.0 |
    # | M8    |    13.0 |    14.0 |     13.0 |   14.5 |
    configs = [
        ('M2', 2.2, 3.8),
        ('M2.5', 2.7, 4.7),
        ('M3', 3.2, 5.7),
        ('M4', 4.3, 7.6),
        ('M5', 5.3, 9.5),
        ('M6', 6.4, 11.0),
        ('M8', 8.4, 14.5),
    ]
    for name, hole_diameter, pad_diameter in configs:
        generate_pkg(
            library='LibrePCB_Base.lplib',
            author='U. Bruhin',
            version='0.1',
            create_date='2025-04-09T15:07:42Z',
            name=name,
            hole_diameter=hole_diameter,
            pad_diameter=pad_diameter,
        )
        generate_dev(
            library='LibrePCB_Base.lplib',
            author='U. Bruhin',
            version='0.1',
            create_date='2025-04-09T15:07:42Z',
            name=name,
            hole_diameter=hole_diameter,
            pad_diameter=pad_diameter,
        )

    save_cache(uuid_cache_file, uuid_cache)
