"""
Generate THT LED packages.
"""
import math
from os import makedirs, path
from uuid import uuid4

from typing import Iterable, List, Optional

from common import format_ipc_dimension as fd
from common import init_cache, now, save_cache
from entities.common import (
    Align, Angle, Author, Category, Created, Deprecated, Description, Fill, GrabArea, Height, Keywords, Layer, Name,
    Polygon, Position, Rotation, Value, Version, Vertex, Width
)
from entities.package import (
    AutoRotate, Drill, Footprint, FootprintPad, LetterSpacing, LineSpacing, Mirror, Package, PackagePad, Shape, Side,
    Size, StrokeText, StrokeWidth
)

generator = 'librepcb-parts-generator (generate_led.py)'

line_width = 0.2
pkg_text_height = 1.0


# Initialize UUID cache
uuid_cache_file = 'uuid_cache_led.csv'
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


class LedConfig:
    def __init__(
        self,
        top_diameter: float,
        bot_diameter: float,
        lead_spacing: float,
        height: float,
    ):
        self.top_diameter = top_diameter
        self.bot_diameter = bot_diameter
        self.lead_spacing = lead_spacing
        self.height = height


def generate_pkg(
    dirpath: str,
    author: str,
    name: str,
    description: str,
    configs: Iterable[LedConfig],
    pkgcat: str,
    keywords: str,
    version: str,
    create_date: Optional[str],
) -> None:
    category = 'pkg'
    for config in configs:
        top_diameter = config.top_diameter
        bot_diameter = config.bot_diameter
        lead_spacing = config.lead_spacing
        height = config.height

        full_name = name.format(
            top_diameter=fd(top_diameter),
            height=fd(height),
        )
        full_description = description.format(
            top_diameter=top_diameter,
            height=height,
            lead_spacing=lead_spacing,
        )

        def _uuid(identifier: str) -> str:
            return uuid(category, full_name, identifier)

        uuid_pkg = _uuid('pkg')

        print('Generating {}: {}'.format(full_name, uuid_pkg))

        # Package
        package = Package(
            uuid=uuid_pkg,
            name=Name(full_name),
            description=Description(full_description),
            keywords=Keywords(keywords),
            author=Author(author),
            version=Version(version),
            created=Created(create_date or now()),
            deprecated=Deprecated(False),
            category=Category(pkgcat),
        )

        # Package pads
        package.add_pad(PackagePad(uuid=_uuid('pad-a'), name=Name('A')))
        package.add_pad(PackagePad(uuid=_uuid('pad-c'), name=Name('C')))

        # Footprint
        footprint = Footprint(
            uuid=_uuid('footprint'),
            name=Name('default'),
            description=Description(''),
        )

        # Footprint pads
        for pad, factor in [('a', 1), ('c', -1)]:
            footprint.add_pad(FootprintPad(
                uuid=_uuid('pad-{}'.format(pad)),
                side=Side.THT,
                shape=Shape.ROUND,
                position=Position(lead_spacing / 2 * factor, 0),
                rotation=Rotation(90),
                size=Size(2.5, 1.3),
                drill=Drill(0.8),
            ))

        # Now the interesting part: The circles with the flattened side.
        # For this, we use a polygon with a circle segment.
        def _generate_flattened_circle(
            identifier: str,
            layer: str,
            outer_radius: float,
            inner_radius: float,
        ) -> Polygon:
            """
            Generate a flattened circle. The flat side will be on the left.
            """
            polygon = Polygon(
                uuid=_uuid(identifier),
                layer=Layer(layer),
                width=Width(line_width),
                fill=Fill(False),
                grab_area=GrabArea(False),
            )

            # To calculate the y offset of the flat side, use Pythagoras
            y = math.sqrt(outer_radius ** 2 - inner_radius ** 2)

            # Now we can calculate the angle of the circle segment
            angle = 360 - math.asin(y / outer_radius) / math.pi * 360

            polygon.add_vertex(Vertex(Position(-inner_radius, -y), Angle(angle)))
            polygon.add_vertex(Vertex(Position(-inner_radius, y), Angle(0)))
            polygon.add_vertex(Vertex(Position(-inner_radius, -y), Angle(0)))
            return polygon

        courtyard_offset = (1.0 if bot_diameter >= 10.0 else 0.8) / 2
        footprint.add_polygon(_generate_flattened_circle(
            identifier='polygon-doc',
            layer='top_documentation',
            outer_radius=bot_diameter / 2 - line_width / 2,
            inner_radius=top_diameter / 2 - line_width / 2,
        ))
        footprint.add_polygon(_generate_flattened_circle(
            identifier='polygon-placement',
            layer='top_placement',
            outer_radius=bot_diameter / 2 + line_width / 2,
            inner_radius=top_diameter / 2 + line_width / 2,
        ))
        footprint.add_polygon(_generate_flattened_circle(
            identifier='polygon-courtyard',
            layer='top_courtyard',
            outer_radius=bot_diameter / 2 + courtyard_offset,
            inner_radius=top_diameter / 2 + courtyard_offset,
        ))

        # Text
        footprint.add_text(StrokeText(
            uuid=_uuid('text-name'),
            layer=Layer('top_names'),
            height=Height(1.0),
            stroke_width=StrokeWidth(0.2),
            letter_spacing=LetterSpacing.AUTO,
            line_spacing=LineSpacing.AUTO,
            align=Align('center bottom'),
            position=Position(0.0, (bot_diameter / 2) + 0.8),
            rotation=Rotation(0.0),
            auto_rotate=AutoRotate(True),
            mirror=Mirror(False),
            value=Value('{{NAME}}'),
        ))
        footprint.add_text(StrokeText(
            uuid=_uuid('text-value'),
            layer=Layer('top_values'),
            height=Height(1.0),
            stroke_width=StrokeWidth(0.2),
            letter_spacing=LetterSpacing.AUTO,
            line_spacing=LineSpacing.AUTO,
            align=Align('center top'),
            position=Position(0.0, -(bot_diameter / 2) - 0.8),
            rotation=Rotation(0.0),
            auto_rotate=AutoRotate(True),
            mirror=Mirror(False),
            value=Value('{{VALUE}}'),
        ))

        # Add footprint to package
        package.add_footprint(footprint)

        pkg_dir_path = path.join(dirpath, uuid_pkg)
        if not (path.exists(pkg_dir_path) and path.isdir(pkg_dir_path)):
            makedirs(pkg_dir_path)
        with open(path.join(pkg_dir_path, '.librepcb-pkg'), 'w') as f:
            f.write('0.1\n')
        with open(path.join(pkg_dir_path, 'package.lp'), 'w') as f:
            f.write(str(package))
            f.write('\n')


if __name__ == '__main__':
    def _make(dirpath: str) -> None:
        if not (path.exists(dirpath) and path.isdir(dirpath)):
            makedirs(dirpath)

    configs = []  # type: List[LedConfig]

    # 5 mm LEDs
    #
    # Note: Common heights determined by looking at the 500 most popular 5mm
    #       THT LEDs on Digikey and plotting a histogram of the heights...
    for height in [8.9, 10.3, 13.3]:
        configs.append(LedConfig(5.00, 5.80, 2.54, height))

    _make('out/led/pkg')
    generate_pkg(
        dirpath='out/led/pkg',
        author='Danilo B.',
        name='LED_THT_D{top_diameter}H{height}_CLEAR_WHITE',
        description='Generic through-hole LED with {top_diameter:.2f} mm'
                    ' body diameter.\\n\\n'
                    'Height: {height:.2f} mm.\\n'
                    'Lead spacing: {lead_spacing:.2f} mm.\\n'
                    'Color: Clear White.',
        configs=configs,
        pkgcat='0a8e9c33-0a23-47e0-a4a5-b1a6c1c7fa2e',
        keywords='led,tht',
        version='0.1',
        create_date='2022-02-26T00:06:03Z',
    )

    save_cache(uuid_cache_file, uuid_cache)
