"""
Generate DO packages.

- JEDEC DO-214 https://www.jedec.org/system/files/docs/DO-214D.PDF

"""
from os import path
from uuid import uuid4

from typing import Optional

from common import format_ipc_dimension as fd
from common import init_cache, now, save_cache
from entities.common import (
    Align, Angle, Author, Category, Created, Deprecated, Description, Fill, GeneratedBy, GrabArea, Height, Keywords,
    Layer, Name, Polygon, Position, Position3D, Rotation, Rotation3D, Value, Version, Vertex, Width
)
from entities.package import (
    AssemblyType, AutoRotate, ComponentSide, CopperClearance, Footprint, FootprintPad, LetterSpacing, LineSpacing,
    Mirror, Package, PackagePad, PackagePadUuid, PadFunction, Shape, ShapeRadius, Size, SolderPasteConfig,
    StopMaskConfig, StrokeText, StrokeWidth
)

GENERATOR_NAME = 'librepcb-parts-generator (generate_do.py)'

line_width = 0.2


# Initialize UUID cache
uuid_cache_file = 'uuid_cache_do.csv'
uuid_cache = init_cache(uuid_cache_file)


def uuid(category: str, full_name: str, identifier: str) -> str:
    key = '{}-{}-{}'.format(category, full_name, identifier).lower().replace(' ', '~')
    if key not in uuid_cache:
        uuid_cache[key] = str(uuid4())
    return uuid_cache[key]


class DoConfig:
    def __init__(
        self,
        body_length_nom: float,
        body_width_nom: float,
        body_height_nom: float,
        total_length_nom: float,
        total_height_nom: float,
        contact_length_min: float,
        contact_length_nom: float,
        contact_length_max: float,
        contact_width_min: float,
        contact_width_max: float,

        variant: str,
        common_name: str,
    ):
        self.body_length = body_length_nom
        self.body_width = body_width_nom
        self.body_height = body_height_nom
        self.total_length = total_length_nom
        self.total_height = total_height_nom
        self.contact_length_min = contact_length_min
        self.contact_length = contact_length_nom
        self.contact_length_max = contact_length_max
        self.contact_width_min = contact_width_min
        self.contact_width = round((contact_width_min + contact_width_max) / 2, 1)
        self.contact_width_max = contact_width_max

        self.variant = variant
        self.common_name = common_name


def generate_pkg(
    library: str,
    author: str,
    config: DoConfig,
    polarity: bool,
    pkgcat: str,
    version: str,
    create_date: Optional[str],
) -> None:
    keywords = f'Diode,SMD,DO-214{config.variant},DO214{config.variant},{config.common_name}'
    polarity_text = 'Unidirectional' if polarity else 'Bidirectional'
    prefix = 'DIOM' if polarity else 'DIONM'
    pkg_name = f'{prefix}{fd(config.total_length, 1)}{fd(config.body_width, 1)}X{fd(config.total_height, 2)}'
    pkg_description = f"""\
{polarity_text} Diode Outline DO-214{config.variant} ({config.common_name}), standardized by JEDEC.

Length: {config.total_length:.2f}mm
Width: {config.body_width:.2f}mm
Height: {config.total_height:.2f}mm

Generated with {GENERATOR_NAME}
"""

    def _uuid(identifier: str) -> str:
        return uuid('pkg', pkg_name, identifier)

    uuid_pkg = _uuid('pkg')

    print('Generating {}: {}'.format(pkg_name, uuid_pkg))

    package = Package(
        uuid=uuid_pkg,
        name=Name(pkg_name),
        description=Description(pkg_description),
        keywords=Keywords(keywords),
        author=Author(author),
        version=Version(version),
        created=Created(create_date or now()),
        deprecated=Deprecated(False),
        generated_by=GeneratedBy(''),
        categories=[Category(pkgcat)],
        assembly_type=AssemblyType.AUTO,
    )

    pads = [('c', 'C', -1), ('a', 'A', 1)] if polarity else [('1', '1', -1), ('2', '2', 1)]

    for pad, name, side in pads:
        package.add_pad(PackagePad(uuid=_uuid('pad-' + pad), name=Name(name)))

    def _rect(
        p: Polygon,
        x0: float,
        x1: float,
        y0: float,
        y1: float,
    ) -> None:
        p.add_vertex(Vertex(Position(x0, y1), Angle(0)))
        p.add_vertex(Vertex(Position(x1, y1), Angle(0)))
        p.add_vertex(Vertex(Position(x1, y0), Angle(0)))
        p.add_vertex(Vertex(Position(x0, y0), Angle(0)))
        p.add_vertex(Vertex(Position(x0, y1), Angle(0)))

    def _pad_center(side: float) -> float:
        return (config.total_length - config.contact_length) / 2 * side

    def _pad_length() -> float:
        return config.contact_length_max + 0.1

    def _pad_width() -> float:
        return config.contact_width_max + 0.35

    def _add_pads(
        footprint: Footprint,
        uuid_ns: str,
    ) -> None:
        for pad, name, side in pads:
            pad_uuid = _uuid(f'pad-{pad}')
            footprint.add_pad(FootprintPad(
                uuid=pad_uuid,
                side=ComponentSide.TOP,
                shape=Shape.ROUNDED_RECT,
                position=Position(_pad_center(side), 0),
                rotation=Rotation(0),
                size=Size(_pad_length(), _pad_width()),
                radius=ShapeRadius(0.0),
                stop_mask=StopMaskConfig.AUTO,
                solder_paste=SolderPasteConfig.AUTO,
                copper_clearance=CopperClearance(0.0),
                function=PadFunction.UNSPECIFIED,
                package_pad=PackagePadUuid(pad_uuid),
                holes=[],
            ))
            lead = Polygon(
                uuid=_uuid(uuid_ns + 'pad-lead'),
                layer=Layer('top_documentation'),
                width=Width(0),
                fill=Fill(True),
                grab_area=GrabArea(False),
            )
            _rect(lead,
                  config.total_length / 2 * side,
                  config.total_length / 2 * side - config.contact_length * side,
                  -config.contact_width / 2,
                  config.contact_width / 2)
            footprint.add_polygon(lead)

    def _add_footprint(
        package: Package,
        name: Name,
        uuid_ns: str,
    ) -> None:
        footprint = Footprint(
            uuid=_uuid(uuid_ns + 'footprint'),
            name=name,
            description=Description(''),
            position_3d=Position3D(0.0, 0.0, 0.0),
            rotation_3d=Rotation3D(0.0, 0.0, 0.0),
        )
        package.add_footprint(footprint)

        top_edge = config.body_width / 2
        bottom_edge = -top_edge
        right_edge = config.body_length / 2
        left_edge = -right_edge
        line_offset = line_width / 2

        #
        # Pads & Leads
        #
        _add_pads(footprint, uuid_ns)

        #
        # Documentation
        #
        outline = Polygon(
            uuid=_uuid(uuid_ns + 'outline'),
            layer=Layer('top_documentation'),
            width=Width(line_width),
            fill=Fill(False),
            grab_area=GrabArea(True),
        )
        _rect(outline,
              left_edge + line_offset, right_edge - line_offset,
              bottom_edge + line_offset, top_edge - line_offset)
        footprint.add_polygon(outline)

        if polarity:
            band = Polygon(
                uuid=_uuid(uuid_ns + 'cathodeband'),
                layer=Layer('top_documentation'),
                width=Width(0),
                fill=Fill(True),
                grab_area=GrabArea(False),
            )
            x0 = _pad_center(-1) + _pad_length() / 2 + 0.2
            x1 = x0 + 0.3
            _rect(band,
                  x0, x1,
                  bottom_edge + line_width, top_edge - line_width)
            footprint.add_polygon(band)

        #
        # Silkscreen
        #
        def _add_silkscreen(
            name: str,
            uuid_ns: str,
        ) -> Polygon:
            return Polygon(
                uuid=_uuid(uuid_ns + 'silkscreen-' + name),
                layer=Layer('top_legend'),
                width=Width(line_width),
                fill=Fill(False),
                grab_area=GrabArea(False),
            )

        if polarity:
            ss = _add_silkscreen('main', uuid_ns)
            x0 = _pad_center(-1) - (_pad_length() / 2 + 0.4)
            x1 = right_edge - line_offset
            y0 = bottom_edge - line_offset
            y1 = top_edge + line_offset
            ss.add_vertex(Vertex(Position(x1, y1), Angle(0)))
            ss.add_vertex(Vertex(Position(x0, y1), Angle(0)))
            ss.add_vertex(Vertex(Position(x0, y0), Angle(0)))
            ss.add_vertex(Vertex(Position(x1, y0), Angle(0)))
            footprint.add_polygon(ss)
        else:
            x0 = left_edge + line_offset
            x1 = right_edge - line_offset
            y0 = bottom_edge - line_offset
            y1 = top_edge + line_offset
            ss = _add_silkscreen('top', uuid_ns)
            ss.add_vertex(Vertex(Position(x0, y1), Angle(0)))
            ss.add_vertex(Vertex(Position(x1, y1), Angle(0)))
            footprint.add_polygon(ss)
            ss = _add_silkscreen('bot', uuid_ns)
            ss.add_vertex(Vertex(Position(x0, y0), Angle(0)))
            ss.add_vertex(Vertex(Position(x1, y0), Angle(0)))
            footprint.add_polygon(ss)

        #
        # Courtyard
        #
        courtyard = Polygon(
            uuid=_uuid(uuid_ns + 'courtyard'),
            layer=Layer('top_courtyard'),
            width=Width(0.0),
            fill=Fill(False),
            grab_area=GrabArea(False),
        )
        _rect(courtyard,
              _pad_center(-1) - (_pad_length() / 2 + 0.4 + line_offset),
              _pad_center(1) + (_pad_length() / 2 + 0.4 + line_offset),
              bottom_edge - line_width,
              top_edge + line_width)
        footprint.add_polygon(courtyard)

        #
        # Text
        #
        footprint.add_text(StrokeText(
            uuid=_uuid(uuid_ns + 'text-name'),
            layer=Layer('top_names'),
            height=Height(1.0),
            stroke_width=StrokeWidth(0.2),
            letter_spacing=LetterSpacing.AUTO,
            line_spacing=LineSpacing.AUTO,
            align=Align('center bottom'),
            position=Position(0.0, top_edge + line_width + 0.5),
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
            position=Position(0.0, bottom_edge - (line_width + 0.5)),
            rotation=Rotation(0.0),
            auto_rotate=AutoRotate(False),
            mirror=Mirror(False),
            value=Value('{{VALUE}}'),
        ))

    _add_footprint(package, Name('default'), 'default-')

    package.serialize(path.join('out', library, 'pkg'))


if __name__ == '__main__':
    configs = []

    # body_length_nom (E1); body_width_nom (D); body_height_nom (A1)
    # total_length_nom (E); total_height_nom (A)
    # contact_length_min, contact_length_nom, contact_length_max (L); contact_width_min, contact_width_max (b)
    # variant; common_name
    configs.append(DoConfig(4.30, 3.60, 2.15,
                            5.40, 2.30,
                            0.75, 1.15, 1.60, 1.95, 2.20,
                            'AA', 'SMB'))

    configs.append(DoConfig(6.85, 5.90, 2.15,
                            7.95, 2.30,
                            0.75, 1.15, 1.60, 2.90, 3.20,
                            'AB', 'SMC'))

    configs.append(DoConfig(4.30, 2.60, 2.30,
                            5.20, 2.40,
                            0.75, 1.15, 1.60, 1.25, 1.65,
                            'AC', 'SMA'))

    configs.append(DoConfig(4.45, 2.60, 2.80,
                            5.25, 2.95,
                            0.75, 1.15, 1.60, 1.00, 1.70,
                            'BA', 'GF1'))

    for config in configs:
        generate_pkg(
            library='LibrePCB_Base.lplib',
            author='murray',
            config=config,
            polarity=True,
            pkgcat='dcaa6b6c-0c55-43fd-a320-5dd74a2cdc85',
            version='0.1',
            create_date='2023-08-15T22:33:08Z',
        )
        generate_pkg(
            library='LibrePCB_Base.lplib',
            author='murray',
            config=config,
            polarity=False,
            pkgcat='dcaa6b6c-0c55-43fd-a320-5dd74a2cdc85',
            version='0.1',
            create_date='2023-08-15T22:33:08Z',
        )

    save_cache(uuid_cache_file, uuid_cache)
