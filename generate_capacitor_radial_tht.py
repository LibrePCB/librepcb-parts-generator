"""
Generate THT polarized radial electrolytic capacitors (CAPPRD).
"""
from os import makedirs, path
from uuid import uuid4

from typing import Optional

from common import format_ipc_dimension, init_cache, now, save_cache
from entities.common import (
    Align, Angle, Author, Category, Circle, Created, Deprecated, Description, Diameter, Fill, GrabArea, Height,
    Keywords, Layer, Name, Polygon, Position, Rotation, Value, Version, Vertex, Width
)
from entities.component import SignalUUID
from entities.device import ComponentPad, ComponentUUID, Device, PackageUUID
from entities.package import (
    AutoRotate, Drill, Footprint, FootprintPad, LetterSpacing, LineSpacing, Mirror, Package, PackagePad, Shape, Side,
    Size, StrokeText, StrokeWidth
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
    dirpath: str,
    diameter: float,
    height: float,
    pitch: float,
    lead_width: float,
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
        )
        footprint.add_pad(FootprintPad(
            uuid=_pkg_uuid('pad-plus'),
            side=Side.THT,
            shape=Shape.RECT,
            position=Position(-pitch / 2, 0),
            rotation=Rotation(0),
            size=Size(pad_diameter, pad_diameter),
            drill=Drill(drill),
        ))
        footprint.add_pad(FootprintPad(
            uuid=_pkg_uuid('pad-minus'),
            side=Side.THT,
            shape=Shape.ROUND,
            position=Position(pitch / 2, 0),
            rotation=Rotation(0),
            size=Size(pad_diameter, pad_diameter),
            drill=Drill(drill),
        ))

        # placement
        footprint.add_circle(Circle(
            uuid=_fpt_uuid('circle-placement'),
            layer=Layer('top_placement'),
            width=Width(0.2),
            fill=Fill(False),
            grab_area=GrabArea(False),
            diameter=Diameter(diameter + 0.2),
            position=Position(0.0, 0.0),
        ))
        footprint.add_polygon(_generate_fill_polygon(
            identifier='polygon-placement-fill',
            layer='top_placement',
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

        # courtyard
        footprint.add_circle(Circle(
            uuid=_fpt_uuid('circle-courtyard'),
            layer=Layer('top_courtyard'),
            width=Width(0.2),
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
    package = Package(
        uuid=_pkg_uuid('pkg'),
        name=Name(name),
        description=Description(
            'Polarized radial electrolytic capacitor.\\n\\n' +
            'Diameter: {} mm\\n'.format(diameter) +
            'Height: {} mm\\n'.format(height) +
            'Lead Spacing: {} mm\\n'.format(pitch) +
            'Max. Lead Diameter: {} mm\\n\\n'.format(lead_width) +
            'Generated with {}'.format(generator)
        ),
        keywords=Keywords('electrolytic,capacitor,polarized,radial,c,cap,cpol'),
        author=Author(author),
        version=Version(version),
        created=Created(create_date or now()),
        deprecated=Deprecated(False),
        category=Category('ee75e31d-f231-41d9-8a3b-bea5114f41e3'),
    )
    package.add_pad(PackagePad(uuid=_pkg_uuid('pad-plus'), name=Name('+')))
    package.add_pad(PackagePad(uuid=_pkg_uuid('pad-minus'), name=Name('-')))
    package.add_footprint(_create_footprint(
        footprint_identifier='default',
        name='default',
    ))

    # write files
    pkg_dir_path = path.join(dirpath, package.uuid)
    if not (path.exists(pkg_dir_path) and path.isdir(pkg_dir_path)):
        makedirs(pkg_dir_path)
    with open(path.join(pkg_dir_path, '.librepcb-pkg'), 'w') as f:
        f.write('0.1\n')
    with open(path.join(pkg_dir_path, 'package.lp'), 'w') as f:
        f.write(str(package))
        f.write('\n')
    print('Wrote package {}'.format(name))


def generate_dev(
    dirpath: str,
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
            'Generic polarized radial electrolytic capacitor.\\n\\n' +
            'Diameter: {} mm\\n'.format(diameter) +
            'Height: {} mm\\n'.format(height) +
            'Lead Spacing: {} mm\\n'.format(pitch) +
            'Max. Lead Diameter: {} mm\\n\\n'.format(lead_width) +
            'Generated with {}'.format(generator)
        ),
        keywords=Keywords('electrolytic,capacitor,polarized,radial,c,cap,cpol'),
        author=Author(author),
        version=Version(version),
        created=Created(create_date or now()),
        deprecated=Deprecated(False),
        category=Category('c011cc6b-b762-498e-8494-d1994f3043cf'),
        component_uuid=ComponentUUID('c54375c5-7149-4ded-95c5-7462f7301ee7'),
        package_uuid=PackageUUID(uuid('pkg', variant, 'pkg')),
    )
    device.add_pad(ComponentPad(
        uuid=uuid('pkg', variant, 'pad-plus'),
        signal=SignalUUID('e010ecbb-6210-4da3-9270-ebd58656dbf0'),
    ))
    device.add_pad(ComponentPad(
        uuid=uuid('pkg', variant, 'pad-minus'),
        signal=SignalUUID('af3ffca8-0085-4edb-a775-fcb759f63411'),
    ))

    # write files
    pkg_dir_path = path.join(dirpath, device.uuid)
    if not (path.exists(pkg_dir_path) and path.isdir(pkg_dir_path)):
        makedirs(pkg_dir_path)
    with open(path.join(pkg_dir_path, '.librepcb-dev'), 'w') as f:
        f.write('0.1\n')
    with open(path.join(pkg_dir_path, 'device.lp'), 'w') as f:
        f.write(str(device))
        f.write('\n')
    print('Wrote device {}'.format(name))


if __name__ == '__main__':

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
            dirpath='out/capacitors_radial_tht/pkg',
            diameter=config['diameter'],
            height=config['height'],
            pitch=config['pitch'],
            lead_width=config['lead_width'],
            author='U. Bruhin',
            version='0.1',
            create_date='2019-12-29T14:14:11Z',
        )
        generate_dev(
            dirpath='out/capacitors_radial_tht/dev',
            diameter=config['diameter'],
            height=config['height'],
            pitch=config['pitch'],
            lead_width=config['lead_width'],
            author='U. Bruhin',
            version='0.1',
            create_date='2019-12-29T14:14:11Z',
        )

    save_cache(uuid_cache_file, uuid_cache)
