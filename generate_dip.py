"""
Generate DIP packages.

There's a JEDEC standard for these packages (JEDEC MS-001D), but it only
describes some of the variations. In the real-world, the actual values vary
quite a lot.

# Standardized package dimensions

## JEDEC MS-001D

+----+--------------+---------------+-----------+------------+
| #  | Package      | Body length   | Lead span | Max height |
+----+--------------+---------------+-----------+------------+
|  8 | BA           |  9.27 (+0.82) |  7.87     | 5.33       |
| 14 | AA           | 19.05 (+1.91) |  7.87     | 5.33       |
| 16 | AB           | 20.07 (+1.14) |  7.87     | 5.33       |
| 16 | BB           | 19.18 (+0.70) |  7.87     | 5.33       |
| 18 | AC           | 22.86 (+1.27) |  7.87     | 5.33       |
| 18 | BC           | 22.10 (+0.89) |  7.87     | 5.33       |
| 20 | AD           | 26.16 (+1.65) |  7.87     | 5.33       |
| 22 | AE           | 29.34 (+1.97) |  7.87     | 5.33       |
| 22 | BD           | 26.16 (+0.38) |  7.87     | 5.33       |
| 24 | AF           | 31.75 (+1.90) |  7.87     | 5.33       |
| 24 | BE           | 30.10 (+1.08) |  7.87     | 5.33       |
| 28 | AG           | 35.69 (+1.33) |  7.87     | 5.33       |
| 28 | BF           | 34.67 (+0.82) |  7.87     | 5.33       |
+----+--------------+---------------+-----------+------------+

Top/bottom offset is between 0.38 mm (BD) and 1.97 mm (AE).
I have no idea how those length values were determined.

# Real-world package dimensions

## Microchip

https://www.microchip.com/quality/packaging-specifications?packageFamily=PDIP

+----+--------------+-------------+-----------+------------+
| #  | Package      | Body length | Lead span | Max height |
+----+--------------+-------------+-----------+------------+
|  8 | PDIP-8 (J7B) |  9.27       |  7.87     | 5.33       |
|    | PDIP-8 (P)   |  9.27       |  7.87     | 5.33       |
|    | PDIP-8 (PA)  |  9.27       |  7.87     | 5.33       |
| 14 | PDIP-14 (P)  | 19.05       |  7.87     | 5.33       |
|    | PDIP-14 (PD) | 19.05       |  7.87     | 5.33       |
| 16 | PDIP-16 (P)  | 19.05       |  7.87     | 5.33       |
|    | PDIP-16 (PE) | 19.05       |  7.87     | 5.33       |
| 18 | PDIP-18 (P)  | 22.86       |  7.87     | 5.33       |
| 20 | PDIP-20 (P)  | 26.16       |  7.87     | 5.33       |
| 24 | PDIP-24 (P)  | 30.99       | 15.44     | 6.35       |
|    | PDIP-24 (PG) | 30.99       | 15.44     | 6.35       |
| 28 | PDIP-28 (P)  | 37.4        | 15.44     | 6.35       |
|    | PDIP-28 (PI) | 37.4        | 15.44     | 6.35       |
| 40 | PDIP-40 (P)  | 51.75       | 15.44     | 6.35       |
|    | PDIP-40 (PL) | 51.75       | 15.44     | 6.35       |
| 64 | PDIP-64 (SP) | 57.66       | 19.51     | 5.08       |
+----+--------------+-------------+-----------+------------+

## TI

https://www.ti.com/packaging/docs/searchtipackages.tsp?packageName=DIP

I excluded special packge sizes like 10/18, which looks like a DIP-18 but with
8 pins missing.

300mil

+----+--------------+-------------+-----------+------------+
| #  | Package      | Body length | Lead span | Max height |
+----+--------------+-------------+-----------+------------+
|  8 | PDIP P       |  9.81       |  7.94     | 5.08       |
|    | PDIP NTC     |  9.53       |  7.94     | 4.19       |
| 14 | PDIP NFF     | 19.18       |  7.94     | 5.33       |
|    | PDIP N       | 19.30       |  7.94     | 5.08       |
| 16 | PDIP NBG     | 21.76       |  7.94     | 5.08       |
|    | PDIP NFG     | 19.30       |  7.94     | 4.32       |
|    | PDIP N       | 19.30       |  7.94     | 5.08       |
|    | PDIP NE      | 19.80       |  7.62     | 5.08       |
| 18 | PDIP NFK     | 22.86       |  7.94     | 5.33       |
|    | PDIP N       | 22.48       |  7.94     | 5.08       |
| 20 | PDIP NFH     | 26.07       |  7.80     | 5.08       |
|    | PDIP N       | 24.33       |  7.94     | 5.08       |
|    | PDIP NE      | 24.51       |  7.62     | 5.08       |
| 24 | PDIP NTG     | 29.91       |  7.81     | 5.33       |
|    | PDIP NAM     | 32.01       |  7.94     | 4.56       |
|    | PDIP NT      | 31.64       |  7.62     | 5.08       |
| 28 | PDIP NT      | 35.69       |  7.75     | 5.08       |
+----+--------------+-------------+-----------+------------+

600mil

+----+--------------+-------------+-----------+------------+
| #  | Package      | Body length | Lead span | Max height |
+----+--------------+-------------+-----------+------------+
| 24 | PDIP NTA     | 30.99       | 15.58     | 6.35 *     |
|    | PDIP NFL     | 31.75       | 15.49     | 7.24 *     |
|    | PDIP N       | 31.75       | 15.24     | 5.08       |
| 28 | PDIP NTD     | 37.40       | 15.57     | 6.35 *     |
|    | PDIP N       | 36.32       | 15.24     | 5.08       |
| 32 | PDIP N       | 41.40       | 15.24     | 5.08       |
| 40 | PDIP NFJ     | 52.26       | 15.49     | 5.33       |
|    | PDIP N       | 52.46       | 15.24     | 5.08       |
| 48 | PDIP N       | 61.47       | 15.24     | 5.08       |
| 52 | PDIP N       | 66.55       | 15.24     | 5.08       |
| 64 | PDIP N       | 81.79       | 23.18     | 5.59 *     |
+----+--------------+-------------+-----------+------------+

# Others

Only some variants are listed.

300mil

+----+--------------+-------------+-----------+------------+
| #  | Manufacturer | Body length | Lead span | Max height |
+----+--------------+-------------+-----------+------------+
|  4 | Toshiba      | 4.58        | 7.62      | 3.90       |
|  6 | Toshiba      | 7.12        | 7.62      | 4.45       |
|  8 | Toshiba      | 9.66        | 7.62      | 4.45       |
+----+--------------+-------------+-----------+------------+

600mil

+----+--------------+-------------+-----------+------------+
| #  | Manufacturer | Body length | Lead span | Max height |
+----+--------------+-------------+-----------+------------+
| 32 | Alliance Mem.| 41.91       | 15.24     | 4.06       |
| 32 | Atmel        | 42.04       | 15.56     | 4.83       |
| 40 | Atmel        | 52.32       | 15.56     | 4.83       |
+----+--------------+-------------+-----------+------------+

# Generated package dimensions

+----+-------------+-----------+------------+------------------+
| #  | Body length | Lead span | Max height | Comment          |
+----+-------------+-----------+------------+------------------+
|  4 |  4.58       |  7.87     | 5.33       | Toshiba          |
|  6 |  7.12       |  7.87     | 5.33       | Toshiba          |
|  8 |  9.65       |  7.87     | 5.33       |                  |
| 14 | 19.05       |  7.87     | 5.33       | JEDEC MS001 AA   |
| 16 | 20.07       |  7.87     | 5.33       | JEDEC MS001 AB   |
| 18 | 22.86       |  7.87     | 5.33       | JEDEC MS001 AC   |
| 20 | 26.16       |  7.87     | 5.33       | JEDEC MS001 AD   |
| 22 | 29.34       |  7.87     | 5.33       | JEDEC MS001 AE   |
| 24 | 31.75       |  7.87     | 5.33       | JEDEC MS001 AF   |
| 28 | 35.69       |  7.87     | 5.33       | JEDEC MS001 AG   |
+----+-------------+-----------+------------+------------------+
| 24 | 31.75       | 15.44     | 5.33       | Like JEDEC MS001 |
| 28 | 37.40       | 15.44     | 5.33       |                  |
| 32 | 42.04       | 15.44     | 5.33       |                  |
| 36 | DEPRECATE   |           |            | No actual usage  |
| 40 | 52.32       | 15.44     | 5.33       |                  |
| 48 | DEPRECATE   |           |            | Almost no usage  |
| 52 | DEPRECATE   |           |            | Almost no usage  |
| 64 | DEPRECATE   |           |            | Almost no usage  |
+----+-------------+-----------+------------+------------------+

"""
from os import makedirs, path
from uuid import uuid4

from typing import Iterable, Optional, Tuple

from common import format_ipc_dimension as ipc
from common import indent, init_cache, save_cache
from entities.common import (
    Align, Angle, Circle, Description, Diameter, Fill, GrabArea, Height, Layer, Name, Polygon, Position, Rotation,
    Value, Vertex, Width
)
from entities.package import (
    AutoRotate, Drill, Footprint, FootprintPad, LetterSpacing, LineSpacing, Mirror, Shape, Side, Size, StrokeText,
    StrokeWidth
)

generator = 'librepcb-parts-generator (generate_dip.py)'

pitch = 2.54
line_width = 0.25
drill_diameter = 0.8
pkg_text_height = 1.0
pkg_text_offset = 0.8
silkscreen_offset = 0.20
pin_package_offset = 0.762  # Distance between drill hole and the package outline
lead_width = 0.55
courtyard_excess = 0.4


# Initialize UUID cache
uuid_cache_file = 'uuid_cache_dip.csv'
uuid_cache = init_cache(uuid_cache_file)


def uuid(category: str, width: str, variant: str, identifier: str) -> str:
    """
    Return a uuid for the specified pin.

    Params:
        category:
            For example 'cmp' or 'pkg'.
        width:
            For example "7.62" or "15.24".
        variant:
            For example '8' or '28'.
        identifier:
            For example 'pad-1' or 'pin-13'.
    """
    key = '{}-{}-{}-{}'.format(category, width, variant, identifier).lower().replace(' ', '~')
    if key not in uuid_cache:
        uuid_cache[key] = str(uuid4())
    return uuid_cache[key]


def get_y(pin_number: int, pin_count: int, spacing: float, grid_align: bool) -> float:
    """
    Return the y coordinate of the specified pin. Keep the pins grid aligned, if desired.

    The pin number is 1 index based. Pin 1 is at the top. The middle pin will
    be at or near 0.

    """
    if grid_align:
        mid = float((pin_count + 1) // 2)
    else:
        mid = (pin_count + 1) / 2
    y = -round(pin_number * spacing - mid * spacing, 2)
    if y == -0.0:  # Returns true for 0.0 too, but that doesn't matter
        return 0.0
    return y


class DipConfig:
    def __init__(
        self,
        pin_count: int,
        body_length: float,
        body_width: float,
        lead_span: float,
        height: float,
        standard: Optional[str] = None,
    ):
        self.pin_count = pin_count
        self.body_length = body_length
        self.body_width = body_width
        self.lead_span = lead_span
        self.height = height
        self.standard = standard


def generate_pkg(
    library: str,
    author: str,
    configs: Iterable[DipConfig],
    pkgcat: str,
    keywords: str,
    create_date: str,
    version: str,
) -> None:
    category = 'pkg'
    for config in configs:
        lines = []

        pin_count = config.pin_count
        variant = '{}pin-D{:.1f}'.format(pin_count, drill_diameter)

        def _uuid(identifier: str) -> str:
            width = '{:.2f}'.format(config.body_width)
            return uuid(category, width, variant, identifier)

        uuid_pkg = _uuid('pkg')
        uuid_pads = [_uuid('pad-{}'.format(p)) for p in range(1, pin_count + 1)]

        # IPC-7251C name:
        # DIP + lead span + W lead width + P pitch + L body length + H component height + Q pin count
        # Example: DIP762 W52 P254 L1905 H508 Q14
        DIP = ipc(config.lead_span)
        W = ipc(lead_width)
        P = pitch * 100
        L = ipc(config.body_length)
        H = ipc(config.height)
        Q = pin_count
        ipc_name = "DIP{}W{}P{:.0f}L{}H{}Q{}".format(DIP, W, P, L, H, Q)

        # Description
        description = "{}-lead DIP (Dual In-Line) package".format(pin_count)
        if config.standard:
            description += " ({})".format(config.standard)
        description += "\\n\\n"
        description += "Pitch: {:.2f}mm\\n".format(pitch)
        description += "Body length: {:.2f}mm\\n".format(config.body_length)
        description += "Body width: {:.2f}mm\\n".format(config.body_width)
        description += "Lead span: {:.2f}mm\\n".format(config.lead_span)
        description += "Lead width: {:.2f}mm\\n".format(lead_width)
        description += "Max height: {:.2f}mm\\n".format(config.height)
        description += "\\nGenerated with {}".format(generator)

        # General info
        lines.append('(librepcb_package {}'.format(uuid_pkg))
        lines.append(' (name "{}")'.format(ipc_name))
        lines.append(' (description "{}")'.format(description))
        lines.append(' (keywords "dip{},pdip{},{}")'.format(pin_count, pin_count, keywords))
        lines.append(' (author "{}")'.format(author))
        lines.append(' (version "{}")'.format(version))
        lines.append(' (created {})'.format(create_date))
        lines.append(' (deprecated false)')
        lines.append(' (category {})'.format(pkgcat))
        for p in range(1, pin_count + 1):
            lines.append(' (pad {} (name "{}"))'.format(uuid_pads[p - 1], p))

        def add_footprint_variant(key: str, name: str, pad_size: Tuple[float, float]) -> None:
            uuid_footprint = _uuid('footprint-{}'.format(key))
            uuid_silkscreen_top = _uuid('polygon-silkscreen-{}'.format(key))
            uuid_silkscreen_bot = _uuid('polygon-silkscreen-bot-{}'.format(key))
            uuid_silkscreen_notch = _uuid('polygon-silkscreen-notch-{}'.format(key))
            uuid_pin1_dot = _uuid('pin1-dot-silkscreen-{}'.format(key))
            uuid_outline = _uuid('polygon-outline-{}'.format(key))
            uuid_courtyard = _uuid('polygon-courtyard-{}'.format(key))
            uuid_text_name = _uuid('text-name-{}'.format(key))
            uuid_text_value = _uuid('text-value-{}'.format(key))

            footprint = Footprint(
                uuid_footprint,
                Name(name),
                Description(''),
            )

            # Pads
            pad_x_offset = float(config.lead_span) / 2
            for p in range(1, pin_count // 2 + 1):
                # Down on the left
                y = get_y(p, pin_count // 2, pitch, False)
                footprint.add_pad(FootprintPad(
                    uuid_pads[p - 1],
                    Side.THT,
                    Shape.RECT if p == 1 else Shape.ROUND,
                    Position(-pad_x_offset, y),
                    Rotation(0.0),
                    Size(pad_size[0], pad_size[1]),
                    Drill(drill_diameter),
                ))
            for p in range(1, pin_count // 2 + 1):
                # Up on the right
                y = -get_y(p, pin_count // 2, pitch, False)
                footprint.add_pad(FootprintPad(
                    uuid_pads[p + pin_count // 2 - 1],
                    Side.THT,
                    Shape.ROUND,
                    Position(pad_x_offset, y),
                    Rotation(0.0),
                    Size(pad_size[0], pad_size[1]),
                    Drill(drill_diameter),
                ))

            # Silkscreen
            silkscreen_top = Polygon(
                uuid_silkscreen_top,
                Layer('top_placement'),
                Width(line_width),
                Fill(False),
                GrabArea(False),
            )
            silkscreen_bot = Polygon(
                uuid_silkscreen_bot,
                Layer('top_placement'),
                Width(line_width),
                Fill(False),
                GrabArea(False),
            )
            silkscreen_notch = Polygon(
                uuid_silkscreen_notch,
                Layer('top_placement'),
                Width(line_width),
                Fill(False),
                GrabArea(False),
            )
            dx = config.body_width / 2 + line_width / 2
            notch_dx = dx / 3
            dy1 = get_y(1, pin_count // 2, pitch, False) \
                + pad_size[1] / 2 \
                + line_width / 2 \
                + silkscreen_offset
            dy2 = config.body_length / 2 + line_width / 2
            silkscreen_top.add_vertex(Vertex(Position(-dx, dy1), Angle(0.0)))
            silkscreen_top.add_vertex(Vertex(Position(-dx, dy2), Angle(0.0)))
            silkscreen_top.add_vertex(Vertex(Position( dx, dy2), Angle(0.0)))
            silkscreen_top.add_vertex(Vertex(Position( dx, dy1), Angle(0.0)))
            footprint.add_polygon(silkscreen_top)
            silkscreen_bot.add_vertex(Vertex(Position(-dx, -dy1), Angle(0.0)))
            silkscreen_bot.add_vertex(Vertex(Position(-dx, -dy2), Angle(0.0)))
            silkscreen_bot.add_vertex(Vertex(Position( dx, -dy2), Angle(0.0)))
            silkscreen_bot.add_vertex(Vertex(Position( dx, -dy1), Angle(0.0)))
            footprint.add_polygon(silkscreen_bot)
            silkscreen_notch.add_vertex(Vertex(Position(-notch_dx, dy2), Angle(0.0)))
            silkscreen_notch.add_vertex(Vertex(Position(-notch_dx, dy2 - line_width), Angle(180.0)))
            silkscreen_notch.add_vertex(Vertex(Position( notch_dx, dy2 - line_width), Angle(0.0)))
            silkscreen_notch.add_vertex(Vertex(Position( notch_dx, dy2), Angle(0.0)))
            footprint.add_polygon(silkscreen_notch)

            # Documentation
            outline = Polygon(
                uuid_outline,
                Layer('top_documentation'),
                Width(line_width),
                Fill(False),
                GrabArea(False),
            )
            dx = config.body_width / 2 - line_width / 2
            dy = config.body_length / 2 - line_width / 2
            outline.add_vertex(Vertex(Position(-dx, dy), Angle(0.0)))  # NW
            outline.add_vertex(Vertex(Position(-notch_dx, dy), Angle(180.0)))
            outline.add_vertex(Vertex(Position(notch_dx, dy), Angle(0.0)))
            outline.add_vertex(Vertex(Position(dx, dy), Angle(0.0)))  # NE
            outline.add_vertex(Vertex(Position(dx, -dy), Angle(0.0)))  # SE
            outline.add_vertex(Vertex(Position(-dx, -dy), Angle(0.0)))  # SW
            outline.add_vertex(Vertex(Position(-dx, dy), Angle(0.0)))  # NW
            footprint.add_polygon(outline)

            # Silkscreen: Pin 1 dot
            pin1_dot_diameter = 0.8
            dx = config.lead_span / 2 + pin1_dot_diameter / 2 + silkscreen_offset
            dy = get_y(1, pin_count // 2, pitch, False) \
                + pad_size[1] / 2 \
                + pin1_dot_diameter / 2 \
                + silkscreen_offset
            pin1_dot = Circle(
                uuid_pin1_dot,
                Layer('top_placement'),
                Width(0.0),
                Fill(True),
                GrabArea(True),
                Diameter(pin1_dot_diameter),
                Position(-dx, dy),
            )
            footprint.add_circle(pin1_dot)

            # Courtyard
            courtyard = Polygon(
                uuid_courtyard,
                Layer('top_courtyard'),
                Width(line_width),
                Fill(False),
                GrabArea(False),
            )
            offset = line_width / 2 + courtyard_excess
            dx_inner = config.body_width / 2 + offset
            dx_outer = pad_x_offset + pad_size[0] / 2 + offset
            dy_inner = get_y(1, pin_count // 2, pitch, False) + pad_size[1] / 2 + offset
            dy_outer = config.body_length / 2 + offset
            courtyard.add_vertex(Vertex(Position(-dx_inner,  dy_outer), Angle(0.0)))  # Top left
            courtyard.add_vertex(Vertex(Position( dx_inner,  dy_outer), Angle(0.0)))  # CW
            courtyard.add_vertex(Vertex(Position( dx_inner,  dy_inner), Angle(0.0)))
            courtyard.add_vertex(Vertex(Position( dx_outer,  dy_inner), Angle(0.0)))
            courtyard.add_vertex(Vertex(Position( dx_outer, -dy_inner), Angle(0.0)))
            courtyard.add_vertex(Vertex(Position( dx_inner, -dy_inner), Angle(0.0)))
            courtyard.add_vertex(Vertex(Position( dx_inner, -dy_outer), Angle(0.0)))
            courtyard.add_vertex(Vertex(Position(-dx_inner, -dy_outer), Angle(0.0)))
            courtyard.add_vertex(Vertex(Position(-dx_inner, -dy_inner), Angle(0.0)))
            courtyard.add_vertex(Vertex(Position(-dx_outer, -dy_inner), Angle(0.0)))
            courtyard.add_vertex(Vertex(Position(-dx_outer,  dy_inner), Angle(0.0)))
            courtyard.add_vertex(Vertex(Position(-dx_inner,  dy_inner), Angle(0.0)))
            courtyard.add_vertex(Vertex(Position(-dx_inner,  dy_outer), Angle(0.0)))
            footprint.add_polygon(courtyard)

            # Labels
            dy = config.body_length / 2 + line_width + pkg_text_offset
            text_attrs = {
                'height': Height(pkg_text_height),
                'stroke_width': StrokeWidth(0.2),
                'letter_spacing': LetterSpacing.AUTO,
                'line_spacing': LineSpacing.AUTO,
                'rotation': Rotation(0.0),
                'auto_rotate': AutoRotate(True),
                'mirror': Mirror(False),
            }
            footprint.add_text(StrokeText(
                uuid_text_name,
                Layer('top_names'),
                align=Align('center bottom'),
                position=Position(0.0, dy),
                value=Value('{{NAME}}'),
                **text_attrs,  # type: ignore # (mypy cannot deal with kwargs)
            ))
            footprint.add_text(StrokeText(
                uuid_text_value,
                Layer('top_values'),
                align=Align('center top'),
                position=Position(0.0, -dy),
                value=Value('{{VALUE}}'),
                **text_attrs,  # type: ignore # (mypy cannot deal with kwargs)
            ))

            lines.extend(indent(1, str(footprint).splitlines()))

        add_footprint_variant('handsoldering', 'hand soldering', (2.54, 1.27))
        add_footprint_variant('compact', 'compact', (1.6, 1.6))

        lines.append(')')

        pkg_dir_path = path.join('out', library, category, uuid_pkg)
        if not (path.exists(pkg_dir_path) and path.isdir(pkg_dir_path)):
            makedirs(pkg_dir_path)
        with open(path.join(pkg_dir_path, '.librepcb-pkg'), 'w') as f:
            f.write('0.1\n')
        with open(path.join(pkg_dir_path, 'package.lp'), 'w') as f:
            f.write('\n'.join(lines))
            f.write('\n')

        print('{}: Wrote package {}'.format(ipc_name, uuid_pkg))


if __name__ == '__main__':
    generate_pkg(
        library='LibrePCB_Base.lplib',
        author='Danilo B.',
        configs=[
            DipConfig(4, 4.58, 7.62, 7.87, 5.33, None),
            DipConfig(6, 7.12, 7.62, 7.87, 5.33, None),
            DipConfig(8, 9.65, 7.62, 7.87, 5.33, None),
            DipConfig(14, 19.05, 7.62, 7.87, 5.33, 'JEDEC MS001 AA'),
            DipConfig(16, 20.07, 7.62, 7.87, 5.33, 'JEDEC MS001 AB'),
            DipConfig(18, 22.86, 7.62, 7.87, 5.33, 'JEDEC MS001 AC'),
            DipConfig(20, 26.16, 7.62, 7.87, 5.33, 'JEDEC MS001 AD'),
            DipConfig(22, 29.34, 7.62, 7.87, 5.33, 'JEDEC MS001 AE'),
            DipConfig(24, 31.75, 7.62, 7.87, 5.33, 'JEDEC MS001 AF'),
            DipConfig(28, 35.69, 7.62, 7.87, 5.33, 'JEDEC MS001 AG'),
        ],
        pkgcat='edc63ee6-ea87-495d-a6b9-54536fe8b1f9',
        keywords='dip,pdip,cdip,cerdip,dual inline package',
        create_date='2018-11-04T23:13:00Z',
        version='0.2',
    )
    generate_pkg(
        library='LibrePCB_Base.lplib',
        author='Danilo B.',
        configs=[
            DipConfig(24, 31.75, 15.24, 15.44, 5.33, None),
            DipConfig(28, 37.40, 15.24, 15.44, 5.33, None),
            DipConfig(32, 42.04, 15.24, 15.44, 5.33, None),
            DipConfig(40, 52.32, 15.24, 15.44, 5.33, None),
        ],
        pkgcat='edc63ee6-ea87-495d-a6b9-54536fe8b1f9',
        keywords='dip,pdip,cdip,cerdip,dual inline package,wide',
        create_date='2018-11-04T23:13:00Z',
        version='0.2',
    )
    save_cache(uuid_cache_file, uuid_cache)
