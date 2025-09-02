"""
Generate IDC style packages.

Implemented so far:

- CNC Tech 3020-xx-0300-00 (2.54 mm pitch)
- CNC Tech 3120-xx-0300-00 (2.00 mm pitch)
- CNC Tech 3220-xx-0300-00 (1.27 mm pitch)

"""
from math import sqrt
from os import path
from uuid import uuid4

from typing import Iterable, Optional, Tuple

from common import init_cache, now, save_cache
from entities.common import (
    Align, Angle, Author, Category, Created, Deprecated, Description, Fill, GeneratedBy, GrabArea, Height, Keywords,
    Layer, Name, Polygon, Position, Position3D, Rotation, Rotation3D, Value, Version, Vertex, Width
)
from entities.component import SignalUUID
from entities.device import ComponentPad, ComponentUUID, Device, Manufacturer, PackageUUID, Part
from entities.package import (
    AssemblyType, AutoRotate, ComponentSide, CopperClearance, Footprint, FootprintPad, LetterSpacing, LineSpacing,
    Mirror, Package, PackagePad, PackagePadUuid, PadFunction, Shape, ShapeRadius, Size, SolderPasteConfig,
    StopMaskConfig, StrokeText, StrokeWidth
)

generator = 'librepcb-parts-generator (generate_idc.py)'

# Global constants
line_width = 0.25
silkscreen_offset = 0.150  # 150 µm
courtyard_offset = 0.5
pkg_text_height = 1.0
sym_text_height = 2.54

# Initialize UUID cache
uuid_cache_file = 'uuid_cache_idc.csv'
uuid_cache = init_cache(uuid_cache_file)

# Initialize UUID cache for connectors
uuid_cache_connectors = init_cache('uuid_cache_connectors.csv')


def uuid(category: str, variant: str, identifier: str) -> str:
    """
    Return a uuid for the specified object.

    Params:
        category:
            For example 'cmp' or 'pkg'.
        variant:
            For example 'cnctech-3020-06-0300' or '1x13'.
        identifier:
            For example 'pad-1' or 'pin-13'.
    """
    key = '{}-{}-{}'.format(category, variant, identifier).lower().replace(' ', '~')
    if key not in uuid_cache:
        uuid_cache[key] = str(uuid4())
    return uuid_cache[key]


class Coord:
    def __init__(self, x: float, y: float, round_values: bool = True):
        if x == -0.0:
            x = 0.0
        if y == -0.0:
            y = 0.0
        if round_values:
            self.x = round(x, 2)
            self.y = round(y, 2)
        else:
            self.x = x
            self.y = y


def get_coords(pin_number: int, pin_count: int, row_count: int, pitch: float, row_spacing: float) -> Coord:
    """
    Return the x/y coordinates of the specified pin.

    The pin number is 1 index based. Pin 1 is at the top left. Pins are
    numbered horizontally, wrapping around.

    Example for 2 rows:

      1 2
      3 4
      5 6

    Example for 3 rows:

      1 2 3
      4 5 6
      7 8 9

    """
    assert pin_count % row_count == 0
    lines = pin_count // row_count

    # For 3 rows, this will be either 0, 1 or 2
    xpos = (pin_number - 1) % row_count
    # Determine x position
    x = xpos * row_spacing - (row_count - 1) * row_spacing / 2

    # For 2 columns and 8 pins, this will be either 0, 1, 2 or 3
    ypos = ((pin_number - 1) // row_count) % (pin_count / row_count)
    # Determine y position
    y = -ypos * pitch + (lines - 1) * pitch / 2

    return Coord(x, y)


class Config:
    def __init__(
        self,
        library: str,
        identifier: str,
        pkg_name: str,
        pkg_author: str,
        pkg_version: str,
        pkg_create_date: str,
        pkg_categories: Iterable[str],
        dev_name: str,
        dev_author: str,
        dev_version: str,
        dev_create_date: str,
        description: str,
        keywords: str,
        pitch: float,
        row_spacing: float,
        pad_size: Tuple[float, float],
        pad_x_offset: float,
        body_offset_x: float,
        body_offset_y: float,
        body_gap: float,
        lead_width: float,
        lead_span: float,
        pin_count: int,
        parts_manufacturer: Optional[str] = None,
        parts_mpn: Optional[Iterable[str]] = None,
    ):
        self.library = library
        self.identifier = identifier.format(pin_count=pin_count)
        self.pkg_name = pkg_name.format(pin_count=pin_count)
        self.pkg_author = pkg_author
        self.pkg_version = pkg_version
        self.pkg_create_date = pkg_create_date
        self.pkg_categories = pkg_categories
        self.dev_name = dev_name.format(pin_count=pin_count)
        self.dev_author = dev_author
        self.dev_version = dev_version
        self.dev_create_date = dev_create_date
        self.description = description.format(pin_count=pin_count) + \
            "\n\nGenerated with {}".format(generator)
        self.keywords = keywords
        self.pitch = pitch
        self.row_spacing = row_spacing
        self.pad_size = pad_size
        self.pad_x_offset = pad_x_offset
        self.body_offset_x = body_offset_x
        self.body_offset_y = body_offset_y
        self.body_gap = body_gap
        self.lead_width = lead_width
        self.lead_span = lead_span
        self.pin_count = pin_count
        self.parts_manufacturer = parts_manufacturer
        self.parts_mpn = [mpn.format(pin_count=pin_count) for mpn in parts_mpn or []]


def generate_pkg(config: Config) -> None:
    def _uuid(identifier: str) -> str:
        return uuid('pkg', config.identifier, identifier)

    uuid_pkg = _uuid('pkg')
    uuid_pads = [_uuid('pad-{}'.format(p)) for p in range(config.pin_count)]
    uuid_leads = [_uuid('lead-{}'.format(p)) for p in range(config.pin_count)]
    uuid_footprint = _uuid('footprint-default')
    uuid_text_name = _uuid('text-name')
    uuid_text_value = _uuid('text-value')
    uuid_legend_north = _uuid('legend-north')
    uuid_legend_south = _uuid('legend-south')
    uuid_doc_contour = _uuid('documentation-contour')
    uuid_doc_triangle = _uuid('documentation-triangle')
    uuid_grab_area = _uuid('grab-area')
    uuid_outline = _uuid('outline')
    uuid_courtyard = _uuid('courtyard')

    package = Package(
        uuid=uuid_pkg,
        name=Name(config.pkg_name),
        description=Description(config.description),
        keywords=Keywords(config.keywords),
        author=Author(config.pkg_author),
        version=Version(config.pkg_version),
        created=Created(config.pkg_create_date or now()),
        deprecated=Deprecated(False),
        generated_by=GeneratedBy(''),
        categories=[Category(cat) for cat in sorted(config.pkg_categories)],
        assembly_type=AssemblyType.SMT,
    )

    for j in range(1, config.pin_count + 1):
        package.add_pad(PackagePad(uuid=uuid_pads[j - 1], name=Name(str(j))))

    footprint = Footprint(
        uuid=uuid_footprint,
        name=Name('default'),
        description=Description(''),
        position_3d=Position3D.zero(),
        rotation_3d=Rotation3D.zero(),
    )
    package.add_footprint(footprint)

    # Pads
    for i in range(1, config.pin_count + 1):
        coords = get_coords(i, config.pin_count, 2, config.pitch, config.row_spacing)
        x_offset_abs = config.pad_size[0] / 2 + config.pad_x_offset
        x_offset = -x_offset_abs if i % 2 == 1 else x_offset_abs
        uuid_pad = uuid_pads[i - 1]
        footprint.add_pad(FootprintPad(
            uuid=uuid_pad,
            side=ComponentSide.TOP,
            shape=Shape.ROUNDED_RECT,
            position=Position(coords.x + x_offset, coords.y),
            rotation=Rotation(0),
            size=Size(*config.pad_size),
            radius=ShapeRadius(0.5),
            stop_mask=StopMaskConfig(StopMaskConfig.AUTO),
            solder_paste=SolderPasteConfig.AUTO,
            copper_clearance=CopperClearance(0),
            function=PadFunction.STANDARD_PAD,
            package_pad=PackagePadUuid(uuid_pad),
            holes=[],
        ))

    # Legs on documentation layer
    for i in range(1, config.pin_count + 1):
        coords = get_coords(i, config.pin_count, 2, config.pitch, config.row_spacing)
        x_offset_abs = config.pad_size[0] / 2 + config.pad_x_offset
        x_offset = -x_offset_abs if i % 2 == 1 else x_offset_abs
        sign = 1 if coords.x > 0 else -1
        footprint.add_polygon(Polygon(
            uuid=uuid_leads[i - 1],
            layer=Layer('top_documentation'),
            width=Width(0),
            fill=Fill(True),
            grab_area=GrabArea(False),
            vertices=[
                Vertex(Position(coords.x - config.lead_width / 2 * sign, coords.y + config.lead_width / 2), Angle(0)),
                Vertex(Position(coords.x - config.lead_width / 2 * sign, coords.y - config.lead_width / 2), Angle(0)),
                Vertex(Position(config.lead_span / 2 * sign, coords.y - config.lead_width / 2), Angle(0)),
                Vertex(Position(config.lead_span / 2 * sign, coords.y + config.lead_width / 2), Angle(0)),
                Vertex(Position(coords.x - config.lead_width / 2 * sign, coords.y + config.lead_width / 2), Angle(0)),
            ],
        ))

    # Body bounds
    pin1 = get_coords(1, config.pin_count, 2, config.pitch, config.row_spacing)
    body_bounds = (
        abs(pin1.x) + config.body_offset_x,
        abs(pin1.y) + config.body_offset_y,
    )
    x_inside_body = body_bounds[0] - line_width / 2
    x_outside_body = body_bounds[0] + line_width / 2
    y_inside_body = body_bounds[1] - line_width / 2
    y_outside_body = body_bounds[1] + line_width / 2

    # Silkscreen
    x_mark_pin1 = abs(pin1.x) + config.pad_size[0] + config.pad_x_offset - line_width / 2
    y_above_pin1 = pin1.y + config.pad_size[1] / 2 + silkscreen_offset + line_width / 2
    # North part contains extended line to mark pin 1
    footprint.add_polygon(Polygon(
        uuid=uuid_legend_north,
        layer=Layer('top_legend'),
        width=Width(line_width),
        fill=Fill(False),
        grab_area=GrabArea(False),
        vertices=[
            Vertex(Position(-x_mark_pin1, y_above_pin1), Angle(0)),
            Vertex(Position(-x_outside_body, y_above_pin1), Angle(0)),
            Vertex(Position(-x_outside_body, y_outside_body), Angle(0)),
            Vertex(Position(x_outside_body, y_outside_body), Angle(0)),
            Vertex(Position(x_outside_body, y_above_pin1), Angle(0)),
        ],
    ))
    # South part doesn't contain any pin markings
    footprint.add_polygon(Polygon(
        uuid=uuid_legend_south,
        layer=Layer('top_legend'),
        width=Width(line_width),
        fill=Fill(False),
        grab_area=GrabArea(False),
        vertices=[
            Vertex(Position(x_outside_body, -y_above_pin1), Angle(0)),
            Vertex(Position(x_outside_body, -y_outside_body), Angle(0)),
            Vertex(Position(-x_outside_body, -y_outside_body), Angle(0)),
            Vertex(Position(-x_outside_body, -y_above_pin1), Angle(0)),
        ],
    ))

    # Documentation layer
    footprint.add_polygon(Polygon(
        uuid=uuid_doc_contour,
        layer=Layer('top_documentation'),
        width=Width(line_width),
        fill=Fill(False),
        grab_area=GrabArea(False),
        vertices=[
            Vertex(Position(-x_inside_body, config.body_gap / 2), Angle(0)),
            Vertex(Position(-x_inside_body, y_inside_body), Angle(0)),
            Vertex(Position(x_inside_body, y_inside_body), Angle(0)),
            Vertex(Position(x_inside_body, -y_inside_body), Angle(0)),
            Vertex(Position(-x_inside_body, -y_inside_body), Angle(0)),
            Vertex(Position(-x_inside_body, -config.body_gap / 2), Angle(0)),
        ],
    ))

    # Triangle on doc layer
    triangle_size = 1.0
    triangle_width = sqrt(3) / 2.0 * triangle_size * 0.8
    triangle_offset = triangle_size / 2  # Offset from doc layer
    footprint.add_polygon(Polygon(
        uuid=uuid_doc_triangle,
        layer=Layer('top_documentation'),
        width=Width(0),
        fill=Fill(True),
        grab_area=GrabArea(False),
        vertices=[
            Vertex(Position(-x_inside_body + triangle_offset, y_inside_body - triangle_offset), Angle(0)),
            Vertex(Position(-x_inside_body + triangle_offset, y_inside_body - triangle_offset - triangle_size), Angle(0)),
            Vertex(Position(-x_inside_body + triangle_offset + triangle_width, y_inside_body - triangle_offset - triangle_size / 2), Angle(0)),
            Vertex(Position(-x_inside_body + triangle_offset, y_inside_body - triangle_offset), Angle(0)),
        ],
    ))

    # Grab area
    footprint.add_polygon(Polygon(
        uuid=uuid_grab_area,
        layer=Layer('top_hidden_grab_areas'),
        width=Width(0),
        fill=Fill(True),
        grab_area=GrabArea(True),
        vertices=[
            Vertex(Position(-body_bounds[0], body_bounds[1]), Angle(0)),
            Vertex(Position(body_bounds[0], body_bounds[1]), Angle(0)),
            Vertex(Position(body_bounds[0], -body_bounds[1]), Angle(0)),
            Vertex(Position(-body_bounds[0], -body_bounds[1]), Angle(0)),
            Vertex(Position(-body_bounds[0], body_bounds[1]), Angle(0)),
        ],
    ))

    # Package outline and courtyard
    def _create_outline(polygon_uuid: str, polygon_layer: str,
                        polygon_offset: float, around_pads: bool) -> Polygon:
        x_outline = body_bounds[0] + polygon_offset
        if around_pads:
            x_outline_extended = abs(pin1.x) + config.pad_size[0] + config.pad_x_offset + polygon_offset
        else:
            x_outline_extended = (config.lead_span / 2) + polygon_offset
        y_outline = body_bounds[1] + polygon_offset
        y_outline_extended = y_above_pin1 + polygon_offset
        return Polygon(
            uuid=polygon_uuid,
            layer=Layer(polygon_layer),
            width=Width(0),
            fill=Fill(False),
            grab_area=GrabArea(False),
            vertices=[
                Vertex(Position(-x_outline_extended, y_outline_extended), Angle(0)),
                Vertex(Position(-x_outline, y_outline_extended), Angle(0)),
                Vertex(Position(-x_outline, y_outline), Angle(0)),
                Vertex(Position(x_outline, y_outline), Angle(0)),
                Vertex(Position(x_outline, y_outline_extended), Angle(0)),
                Vertex(Position(x_outline_extended, y_outline_extended), Angle(0)),
                Vertex(Position(x_outline_extended, -y_outline_extended), Angle(0)),
                Vertex(Position(x_outline, -y_outline_extended), Angle(0)),
                Vertex(Position(x_outline, -y_outline), Angle(0)),
                Vertex(Position(-x_outline, -y_outline), Angle(0)),
                Vertex(Position(-x_outline, -y_outline_extended), Angle(0)),
                Vertex(Position(-x_outline_extended, -y_outline_extended), Angle(0)),
            ],
        )
    footprint.add_polygon(_create_outline(uuid_outline, 'top_package_outlines', 0, False))
    footprint.add_polygon(_create_outline(uuid_courtyard, 'top_courtyard', courtyard_offset, True))

    # Labels
    body_y_max = (config.pin_count / 2 - 1) * config.pitch / 2 + config.body_offset_y
    footprint.add_text(StrokeText(
        uuid=uuid_text_name,
        layer=Layer('top_names'),
        height=Height(pkg_text_height),
        stroke_width=StrokeWidth(0.2),
        letter_spacing=LetterSpacing.AUTO,
        line_spacing=LineSpacing.AUTO,
        align=Align('center bottom'),
        position=Position(0.0, body_y_max + 1),
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
        position=Position(0.0, -body_y_max - 1),
        rotation=Rotation(0.0),
        auto_rotate=AutoRotate(True),
        mirror=Mirror(False),
        value=Value('{{VALUE}}'),
    ))

    # Approvals
    package.add_approval(
        "(approved missing_footprint_3d_model\n" +
        " (footprint {})\n".format(uuid_footprint) +
        ")"
    )

    package.serialize(path.join('out', config.library, 'pkg'))
    print('Wrote package {}: {}'.format(uuid_pkg, config.pkg_name))


def generate_dev(config: Config) -> None:
    def _uuid(category: str, identifier: str) -> str:
        return uuid(category, config.identifier, identifier)

    def _uuid_cmp(identifier: str) -> str:
        variant = '{}x{}'.format(2, config.pin_count // 2)
        key = 'cmp-pinheader-{}-{}'.format(variant, identifier).lower().replace(' ', '~')
        return uuid_cache_connectors[key]

    uuid_dev = _uuid('dev', 'dev')
    uuid_pkg = _uuid('pkg', 'pkg')
    uuid_pads = [_uuid('pkg', 'pad-{}'.format(p)) for p in range(config.pin_count)]
    uuid_cmp = _uuid_cmp('cmp')
    uuid_signals = [_uuid_cmp('signal-{}'.format(p)) for p in range(config.pin_count)]

    device = Device(
        uuid=uuid_dev,
        name=Name(config.dev_name),
        description=Description(config.description),
        keywords=Keywords(config.keywords),
        author=Author(config.dev_author),
        version=Version(config.dev_version),
        created=Created(config.dev_create_date or now()),
        deprecated=Deprecated(False),
        generated_by=GeneratedBy(''),
        categories=[Category('4a4e3c72-94fb-45f9-a6d8-122d2af16fb1')],
        component_uuid=ComponentUUID(uuid_cmp),
        package_uuid=PackageUUID(uuid_pkg),
    )

    for i in range(1, config.pin_count + 1):
        device.add_pad(ComponentPad(
            pad_uuid=uuid_pads[i - 1],
            signal=SignalUUID(uuid_signals[i - 1]),
        ))

    for mpn in config.parts_mpn:
        device.add_part(Part(
            mpn=mpn, manufacturer=Manufacturer(config.parts_manufacturer or '')
        ))

    # write files
    device.serialize(path.join('out', config.library, 'dev'))
    print('Wrote device {}: {}'.format(uuid_dev, config.dev_name))


if __name__ == '__main__':
    # CNC Tech
    configs = \
        [Config(
            library='CNC_Tech.lplib',
            identifier='cnctech-3220-{pin_count}-0300',
            pkg_name='CNCTECH_3220-{pin_count:02}-0300-XX',
            pkg_author='Danilo Bargen',
            pkg_version='0.2',
            pkg_create_date='2019-07-09T21:31:21Z',
            pkg_categories=['92186130-e1a4-4a82-8ce9-88f4aa854195', 'e4d3a6bf-af32-48a2-b427-5e794bed949a'],
            dev_name='CNC Tech 3220-{pin_count:02}-0300',
            dev_author='U. Bruhin',
            dev_version='0.2',
            dev_create_date='2019-10-19T10:11:49Z',
            description='{pin_count}-pin 1.27mm pitch SMD IDC box header by CNC Tech.',
            keywords='cnc tech,idc,header,male,box header,smd,3220,1.27mm',
            pitch=1.27,
            row_spacing=1.27,
            pad_size=(2.4, 0.76),
            pad_x_offset=0.115,
            body_offset_x=1.915,
            body_offset_y=3.785,
            body_gap=2.35,
            lead_width=0.4,
            lead_span=5.5,
            pin_count=pc,
            parts_manufacturer='CNC Tech',
            parts_mpn=['3220-{pin_count:02}-0300-00', '3220-{pin_count:02}-0300-00-TR'],
        ) for pc in [10, 14, 16, 20, 26, 30, 34, 40, 50, 60]] + \
        [Config(
            library='CNC_Tech.lplib',
            identifier='cnctech-3120-{pin_count}-0300',
            pkg_name='CNCTECH_3120-{pin_count:02}-0300-XX',
            pkg_author='Danilo Bargen',
            pkg_version='0.2',
            pkg_create_date='2019-07-09T21:31:21Z',
            pkg_categories=['92186130-e1a4-4a82-8ce9-88f4aa854195', 'e4d3a6bf-af32-48a2-b427-5e794bed949a'],
            dev_name='CNC Tech 3120-{pin_count:02}-0300',
            dev_author='U. Bruhin',
            dev_version='0.2',
            dev_create_date='2023-08-29T17:06:05Z',
            description='{pin_count}-pin 2.00mm pitch SMD IDC box header by CNC Tech.',
            keywords='cnc tech,idc,header,male,box header,smd,3120,2.00mm',
            pitch=2.0,
            row_spacing=2.0,
            pad_size=(3.45, 0.9),
            pad_x_offset=-0.2,
            body_offset_x=1.75,
            body_offset_y=4.65,
            body_gap=3.7,
            lead_width=0.5,
            lead_span=7.5,
            pin_count=pc,
            parts_manufacturer='CNC Tech',
            parts_mpn=['3120-{pin_count:02}-0300-00'],  # No '-TR' variant(?)
        ) for pc in [6, 8, 10, 12, 14, 16, 18, 20, 24, 26, 30, 34, 40, 44, 50, 60, 64]] + \
        [Config(
            library='CNC_Tech.lplib',
            identifier='cnctech-3020-{pin_count}-0300',
            pkg_name='CNCTECH_3020-{pin_count:02}-0300-XX',
            pkg_author='Danilo Bargen',
            pkg_version='0.2',
            pkg_create_date='2019-07-09T21:31:21Z',
            pkg_categories=['92186130-e1a4-4a82-8ce9-88f4aa854195', 'e4d3a6bf-af32-48a2-b427-5e794bed949a'],
            dev_name='CNC Tech 3020-{pin_count:02}-0300',
            dev_author='U. Bruhin',
            dev_version='0.2',
            dev_create_date='2023-08-29T17:06:05Z',
            description='{pin_count}-pin 2.54mm pitch SMD IDC box header by CNC Tech.',
            keywords='cnc tech,idc,header,male,box header,smd,3020,2.54mm',
            pitch=2.54,
            row_spacing=2.54,
            pad_size=(4.8, 0.9),
            pad_x_offset=-0.42,
            body_offset_x=3.13,
            body_offset_y=5.08,
            body_gap=5.08,
            lead_width=0.64,
            lead_span=10.2,
            pin_count=pc,
            parts_manufacturer='CNC Tech',
            parts_mpn=['3020-{pin_count:02}-0300-00', '3020-{pin_count:02}-0300-00-TR'],
        ) for pc in [6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 40, 44, 50, 60, 64]]
    for config in configs:
        generate_pkg(config=config)
        generate_dev(config=config)

    save_cache(uuid_cache_file, uuid_cache)
