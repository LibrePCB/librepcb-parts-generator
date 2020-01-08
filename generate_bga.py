"""
Generate the following  packages:

- BGA ( JEDEC MO-216)


"""
from os import makedirs, path
from uuid import uuid4

from typing import Dict, Iterable, List, Optional

from common import format_float as ff
from common import format_ipc_dimension as fd
from common import generate_courtyard, indent, init_cache, now, save_cache

generator = 'librepcb-parts-generator (generate_bga.py)'

line_width        = 0.25  #
pkg_text_height   = 1.0   #
silkscreen_offset = 0.8   #
silkscreen_pin_1  = 0.9   #
courtyard_excess  = 0.5   #
label_offset      = 1.27  #

# Initialize UUID cache
uuid_cache_file = 'uuid_cache_bga.csv'
uuid_cache = init_cache(uuid_cache_file)


def uuid(category: str, full_name: str, identifier: str) -> str:
    """
    Return a uuid for the specified pin.

    Params:
        category:
            For example 'cmp' or 'pkg'.
        full_name:
            For example "BGA".
        identifier:
            For example 'pad-1' or 'pin-13'.
    """
    key = '{}-{}-{}'.format(category, full_name, identifier).lower().replace(' ', '~')
    if key not in uuid_cache:
        uuid_cache[key] = str(uuid4())
    return uuid_cache[key]





class BgaConfig:
    def __init__(
        self,
        pin_count: int,
        row_count: int,
        pitch: float,
        ball_width: float,
        body_width: float,
        height: float,
        variation: Optional[str] = None,
    ):
        self.pin_count = pin_count
        self.row_count = row_count
        self.pitch = pitch
        self.ball_width = ball_width
        self.body_width = body_width
        self.height = height
        self.variation = variation


def generate_pkg(
    dirpath: str,
    author: str,
    name: str,
    description: str,
    configs: Iterable[BgaConfig],
    row_lookup: Dict[int, str],
    pkgcat: str,
    keywords: str,
    version: str,
    create_date: Optional[str],
) -> None:
    category = 'pkg'
    for config in configs:
        pitch = config.pitch
        pin_count = config.pin_count
        row_count = config.row_count
        height = config.height
        body_width = config.body_width
        ball_width = config.ball_width


        lines = []
        balls = []
        full_name = name.format(
            height=fd(height),
            pitch=fd(pitch),
            pin_count=pin_count,
            row_count=row_count,
            body_width=fd(body_width),
            ball_width=fd(ball_width),

        )
        full_description = description.format(
            height=height,
            pin_count=pin_count,
            row_count=row_count,
            pitch=pitch,
            body_width=body_width,
            ball_width=ball_width,
            variation=config.variation,
        )

        def _uuid(identifier: str) -> str:
            return uuid(category, full_name, identifier)

        uuid_pkg = _uuid('pkg')


        print('Generating {}: {}'.format(full_name, uuid_pkg))

        # General info
        lines.append('(librepcb_package {}'.format(uuid_pkg))
        lines.append(' (name "{}")'.format(full_name))
        lines.append(' (description "{}\\n\\nGenerated with {}")'.format(full_description, generator))
        lines.append(' (keywords "{}")'.format(keywords))
        lines.append(' (author "{}")'.format(author))
        lines.append(' (version "{}")'.format(version))
        lines.append(' (created {})'.format(create_date or now()))
        lines.append(' (deprecated false)')
        lines.append(' (category {})'.format(pkgcat))



        for p in range(1, pin_count + 1):
            xo =   ( (p-1)  % row_count)+1    
            yo =   ( (p-1) // row_count)
            Zo=    row_lookup[yo]
            balls.append ( "%s%s"%(Zo,xo))





        uuid_pads = [_uuid('pad-{}'.format(balls[p-1])) for p in range(1, pin_count + 1)]

        for p in range(1, pin_count + 1):
            lines.append(' (pad {} (name "{}"))'.format(uuid_pads[p - 1], balls[p-1]))


            
        def add_footprint_variant(
            key: str,
            name: str,
            density_level: str,
        ) -> None:
            uuid_footprint = _uuid('footprint-{}'.format(key))
            uuid_silkscreen_top = _uuid('polygon-silkscreen-{}'.format(key))
            uuid_silkscreen_bot = _uuid('polygon-silkscreen2-{}'.format(key))
            uuid_outline = _uuid('polygon-outline-{}'.format(key))
            uuid_courtyard = _uuid('polygon-courtyard-{}'.format(key))
            uuid_text_name = _uuid('text-name-{}'.format(key))
            uuid_text_value = _uuid('text-value-{}'.format(key))

            lines.append(' (footprint {}'.format(uuid_footprint))
            lines.append('  (name "{}")'.format(name))
            lines.append('  (description "")')


            # Pads

            mid =   round( ((row_count / 2 ) - .5) * pitch,3)
            for p in range(0, pin_count  ):

                pxo =   round( ((p  % row_count) * pitch) - mid , 3)  
                y = -round((p // row_count)*pitch,3) + mid 
                pad_uuid = uuid_pads[p ]
                lines.append('  (pad {} (side top) (shape round)'.format(pad_uuid))
                lines.append('   (position {} {}) (rotation 0.0) (size {} {}) (drill 0.0)'.format(
                    pxo, ff(y), ff(ball_width), ff(ball_width),
                ))
                lines.append('  )')





            # Silkscreen (fully outside body)
            # Ensure minimum clearance between copper and silkscreen
            y_offset = silkscreen_offset
            short_y_max = ff(body_width / 2 + y_offset - silkscreen_pin_1)
            y_max = ff(body_width / 2 + y_offset)
            y_min = ff(-body_width / 2 - y_offset)
            short_x_offset = silkscreen_offset -silkscreen_pin_1+ (body_width / 2)
            x_offset = silkscreen_offset + (body_width / 2)
            
            lines.append('  (polygon {} (layer top_placement)'.format(uuid_silkscreen_top))
            lines.append('   (width {}) (fill false) (grab_area false)'.format(line_width))
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(ff(-short_x_offset), y_max))  # noqa
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(ff(x_offset), y_max))  # noqa
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(ff(x_offset), y_min))  # noqa
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(ff(-x_offset), y_min))  # noqa
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(ff(-x_offset), short_y_max))  # noqa
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(ff(-short_x_offset), y_max))  # noqa
            lines.append('  )')

            # Documentation outline (fully inside body)
            outline_x_offset = body_width/2   -line_width /2
            lines.append('  (polygon {} (layer top_documentation)'.format(uuid_outline))
            lines.append('   (width {}) (fill false) (grab_area true)'.format(line_width))
            y_max = ff(body_width/2  -line_width /2)
            y_min = ff(-body_width/2  +line_width /2)
            oxo = ff(outline_x_offset)  # Used for shorter code lines below :)
            lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(oxo, y_max))
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(oxo, y_max))
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(oxo, y_min))
            lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(oxo, y_min))
            lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(oxo, y_max))
            lines.append('  )')


            # Max boundaries (pads or body)
                
            max_x =  body_width / 2 
            max_y =  body_width / 2

            # Courtyard
 
            lines.extend(indent(2, generate_courtyard(
                uuid=uuid_courtyard,
                max_x=max_x,
                max_y=max_y,
                excess_x=courtyard_excess,
                excess_y=courtyard_excess,
            )))

            # Labels
            y_max = ff(body_width /  2 + label_offset)
            y_min = ff(-body_width / 2 - label_offset)
            text_attrs = '(height {}) (stroke_width 0.2) ' \
                         '(letter_spacing auto) (line_spacing auto)'.format(pkg_text_height)
            lines.append('  (stroke_text {} (layer top_names)'.format(uuid_text_name))
            lines.append('   {}'.format(text_attrs))
            lines.append('   (align center bottom) (position 0.0 {}) (rotation 0.0)'.format(y_max))
            lines.append('   (auto_rotate true) (mirror false) (value "{{NAME}}")')
            lines.append('  )')
            lines.append('  (stroke_text {} (layer top_values)'.format(uuid_text_value))
            lines.append('   {}'.format(text_attrs))
            lines.append('   (align center top) (position 0.0 {}) (rotation 0.0)'.format(y_min))
            lines.append('   (auto_rotate true) (mirror false) (value "{{VALUE}}")')
            lines.append('  )')

            lines.append(' )')

        add_footprint_variant('density~b', 'Reflow nom', 'nom')
        lines.append(')')

        pkg_dir_path = path.join(dirpath, uuid_pkg)
        if not (path.exists(pkg_dir_path) and path.isdir(pkg_dir_path)):
            makedirs(pkg_dir_path)
        with open(path.join(pkg_dir_path, '.librepcb-pkg'), 'w') as f:
            f.write('0.1\n')
        with open(path.join(pkg_dir_path, 'package.lp'), 'w') as f:
            f.write('\n'.join(lines))
            f.write('\n')


if __name__ == '__main__':
    def _make(dirpath: str) -> None:
        if not (path.exists(dirpath) and path.isdir(dirpath)):
            makedirs(dirpath)


    # BGA

    _make('out/bga/pkg')
    generate_pkg(
        dirpath='out/bga/pkg',
        author='John E.',
        # Name according to IPC7351C
        name='BGA{pin_count}N{pitch}P{row_count}X{row_count}_{body_width}X{body_width}X{height}B{ball_width}',
        description='{pin_count}-pin Plastic Bottom Grid Array Ball (PBGA-B), '
                    'standardized by JEDEC (MO-216), variation {variation}.\\n\\n'
                    'Pitch: {pitch:.2f} mm\\nBody length: {body_width:.2f} mm\\n'
                    'Body width: {body_width:.2f} mm\\n'
                    'Height: {height:.2f} mm\\n'
                    'Ball width: {ball_width:.2f} mm',
        configs=[
       #               pin   row  pitch  ball   body      height variation
       #              count count        width  width    
            BgaConfig(  36,   6,  0.40,  0.25,  2.50,      1.00,    'ucBGA'),
            BgaConfig(  49,   7,  0.40,  0.25,  3.00,      1.00,    'ucBGA'),
            BgaConfig(  64,   8,  0.40,  0.25,  4.00,      1.00,    'ucBGA'),
            BgaConfig(  81,   9,  0.40,  0.25,  4.00,      1.00,    'ucBGA'),
            BgaConfig( 121,  11,  0.40,  0.25,  5.00,      1.00,    'ucBGA'),
            BgaConfig( 121,  11,  0.50,  0.25,  6.00,      1.00,    'csBGA'),
            BgaConfig( 121,  11,  0.80,  0.40,  9.00,      1.10,    'caBGA'),
            BgaConfig( 225,  15,  0.40,  0.25,  7.00,      1.00,    'ucBGA'),
            BgaConfig( 256,  16,  0.80,  0.45,  14.0,      1.70,    'caBGA'),
        ],
        row_lookup={
            0: "A",
            1: "B",
            2: "C",
            3: "D",
            4: "E",
            5: "F",
            6: "G",
            7: "H",
            8: "J",
            9: "K",
            10: "L",
            11: "M",
            12: "N",
            13: "P",
            14: "R",
            15: "T",
            16: "U",
            17: "V",
            18: "W",
            19: "Z",
            20: "BA",
            21: "BB",
            22: "BC",
            23: "BD",
            24: "BE",
            25: "BF",
            26: "BG",
            27: "BH",
            28: "BJ",
            29: "BK",
            30: "BL",
            31: "BM",
            32: "BN",
            
        },
        pkgcat='a1216e37-110e-4abc-b896-4b74fe38684c',
        keywords='bga, package,smd,jedec,MO-216',
        version='0.1',
        create_date='2019-12-13T12:00:00Z',
    )
    save_cache(uuid_cache_file, uuid_cache)
