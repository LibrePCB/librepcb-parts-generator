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
        col_count: int,
        pitch: float,
        ball_width: float,
        body_width: float,
        body_length: float,
        height: float,
        mask: int,    
        variation: Optional[str] = None,
    ):
        self.pin_count = pin_count
        self.row_count = row_count
        self.col_count = col_count
        self.pitch = pitch
        self.ball_width = ball_width
        self.body_width = body_width
        self.body_length = body_length
        self.height = height
        self.mask   = mask
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
        col_count = config.col_count
        height = config.height
        body_width = config.body_width
        body_length = config.body_length
        ball_width = config.ball_width
        mask  = config.mask

        lines  = []
        
        
        full_name = name.format(
            height=fd(height),
            pitch=fd(pitch),
            pin_count=pin_count,
            row_count=row_count,
            col_count=col_count,
            body_width=fd(body_width),
            body_length=fd(body_length),
            ball_width=fd(ball_width),
            mask=mask,

        )
        full_description = description.format(
            height=height,
            pin_count=pin_count,
            row_count=row_count,
            col_count=col_count,
            pitch=pitch,
            body_width=body_width,
            body_length=body_length,
            ball_width=ball_width,
            mask=mask,
            variation=config.variation,
        )

        def _uuid(identifier: str) -> str:
            return uuid(category, full_name, identifier)

        uuid_pkg = _uuid('pkg')
        uuid_pads = []

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

        max_pin_count = row_count * col_count
   
        S_mask = mask     
        for p in range(1, max_pin_count + 1):
            m =  (S_mask % 2) 

            if m :
               xo =   ( (p-1)  % col_count)+1    
               yo=    row_lookup[ (p-1) // row_count  ]
               uuid_pads.append(_uuid('pad-{}'.format("%s%s"%(yo,xo))))
               lines.append(' (pad {} (name "{}"))'.format( _uuid('pad-{}'.format("%s%s"%(yo,xo)))     , "%s%s"%(yo,xo)))
            S_mask = S_mask >> 1

            
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
            pad_pointer=0
            S_mask = mask     
            for p in range(0, max_pin_count  ):
              m =  (S_mask % 2) 

              if m :
                pxo =   round( ((p  % col_count) * pitch) - mid , 3)  
                y = -round((p // row_count)*pitch,3) + mid 
                pad_uuid = uuid_pads[pad_pointer ]
                pad_pointer = pad_pointer+1
                lines.append('  (pad {} (side top) (shape round)'.format(pad_uuid))
                lines.append('   (position {} {}) (rotation 0.0) (size {} {}) (drill 0.0)'.format(
                    pxo, ff(y), ff(ball_width), ff(ball_width),
                ))
                lines.append('  )')
              S_mask = S_mask >> 1




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
        name='BGA{pin_count}N{pitch}P{row_count}X{col_count}_{body_width}X{body_length}X{height}B{ball_width}',
        description='{pin_count}-pin Plastic Bottom Grid Array Ball (PBGA-B), '
                    'standardized by JEDEC (MO-216), variation {variation}.\\n\\n'
                    'Pitch: {pitch:.2f} mm\\nBody length: {body_length:.2f} mm\\n'
                    'Body width: {body_width:.2f} mm\\n'
                    'Height: {height:.2f} mm\\n'
                    'Ball width: {ball_width:.2f} mm',
        configs=[
       #               pin   row   col   pitch  ball   body    body  height  mask variation
       #              count count count         width  width  length

       #         4 x 4     
            BgaConfig(  16,   4,     4,  0.35,  0.25,   1.48,    1.40, 0.452,
                        0b1111111111111111,  'WLCSopt1' ),

            BgaConfig(  16,   4,     4,  0.35,  0.25,   1.409,    1.409, 0.452,
                        0b1111111111111111,  'WLCSopt12' ),
            

       #         5 x 5     
            BgaConfig(  25,   5,     5,  0.40,  0.25,   2.546,    2.492, 0.575,
                        0b1111111111111111111111111, 'WLCS' ),
            BgaConfig(  25,   5,     5,  0.35,  0.25,   1.71,    1.71, 0.452,
                        0b1111111111111111111111111, 'WLCS' ),



            
       #         6 x 6     
            BgaConfig(  36,   6,     6,  0.40,  0.25,  2.50,   2.50,  1.00,
                        0b111111111111111111111111111111111111, 'ucBGA'),


            BgaConfig(  36,   6,     6,  0.35,  0.25,  2.078,   2.078,  0.452,
                        0b111111111111111111111111111111111111, 'WLCSopt1'),


      #         7 x 7     
            BgaConfig(  49,   7,     7,  0.40,  0.25,  3.00,   3.00,  1.00,
                        0b1111111111111111111111111111111111111111111111111,   'ucBGA'),
            BgaConfig(  49,   7,     7,  0.80,  0.46,  7.00,   7.00,  1.40,
                        0b1111111111111111111111111111111111111111111111111,    'caBGA'),
            BgaConfig(  49,   7,     7,  0.40,  0.25,  3.185,   3.106,  0.60,
                        0b1111111111111111111111111111111111111111111111111,    'WLCS'),




            

      #         8 x 8     
            BgaConfig(  64,   8,     8,  0.40,  0.25,  4.00,   4.00,  1.00,
                        0b1111111111111111111111111111111111111111111111111111111111111111,   'ucBGA'),
            BgaConfig(  64,   8,     8,  0.50,  0.30,  5.00,   5.00,  1.00,
                        0b1111111111111111111111111111111111111111111111111111111111111111,   'csBGA'),
       #         9 x 9     
            BgaConfig(  81,   9,     9,  0.50,  0.25,  5.00,   5.00,  1.00,
                        0b111111111111111111111111111111111111111111111111111111111111111111111111111111111,    'csBGA'),
            BgaConfig(  81,   9,     9,  0.40,  0.25,  4.00,   4.00,  1.00,
                        0b111111111111111111111111111111111111111111111111111111111111111111111111111111111,  'ucBGA'),
            BgaConfig(  81,   9,     9,  0.40,  0.25,  3.693,   3.797,  0.543,
                        0b111111111111111111111111111111111111111111111111111111111111111111111111111111111,   'WLCS' ),

            

       #         10 x 10     
            BgaConfig(  56,  10,    10,  0.50,  0.30,  6.00,   6.00,  1.23,
                        0b1111111111100000000110111111011010000101101000010110100001011010000101101111110110000000011111111111,    'csBGA'),
 
            BgaConfig( 100,  10,    10,  0.80,  0.46, 10.00,  10.00,  1.40,
                        0b1111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111,   'caBGA'),
            BgaConfig( 100,  10,    10,  1.00,  0.55, 11.00,  11.00,  1.50,
                        0b1111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111,   'fpBGA'),

       #         11 x 11     
            BgaConfig( 121,  11,    11,  0.40,  0.25,  5.00,   5.00,  1.00,
                        0b1111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111,  'ucBGA'),
            BgaConfig( 121,  11,    11,  0.50,  0.25,  6.00,   6.00,  1.00,
                        0b1111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111,  'csBGA'),
            BgaConfig( 121,  11,    11,  0.80,  0.40,  9.00,   9.00,  1.10,
                        0b1111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111,  'caBGA'),

       #         12 x 12                 
            BgaConfig( 132,  12,    12,  0.40,  0.25,   6.0,   6.00,  1.00,
                        0b111111111111111111111111111111111111111111111111111110011111111100001111111100001111111110011111111111111111111111111111111111111111111111111111,  'ucBGA'),
            BgaConfig( 144,  12,    12,  0.50,  0.30,   7.0,   7.00,  1.00,
                        0b111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111,  'csBGA'),
            BgaConfig( 144,  12,    12,  1.00,  0.60,  13.0,   13.0,  1.70,
                        0b111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111,  'fpBGA'),




            
       #         14 x 14     
            BgaConfig( 100,  14,    14,  0.50,  0.30,  8.00,   8.00,  1.23,
             0b1111111111111111111111111111111000000001111100000000001111000000000011110000000000111100000000001111000000000011110000000000111100000000001111000000000011111000000001111111111111111111111111111111, 'csBGA'),
            BgaConfig( 132,  14,    14,  0.50,  0.30,   8.00,   8.00,  1.23,
                        0b1111111111111111111111111111111111111111111110000000011111100000000111111000000001111110000000011111100000000111111000000001111110000000011111100000000111111111111111111111111111111111111111111111,   'csBGAopt1'),



            BgaConfig( 132,  14,    14,  0.50,  0.30,   8.00,   8.00,  1.00,
             0b1111111111111110000000000001101111111111011011111111110110110000001101101101111011011011011110110110110111101101101101111011011011000000110110111111111101101111111111011000000000000111111111111111,   'csBGAopt2'),

            
            BgaConfig( 184,  14,    14,  0.50,  0.30,   8.00,   8.00,  1.35,
                    0b1111111111111111111111111111111111111111111111111111111111110011001111111101111011111111111111111111111111111111111101111011111111001100111111111111111111111111111111111111111111111111111111111111,'csBGA'),



            
            BgaConfig( 196,  14,    14,  0.50,  0.30,   8.00,   8.00,  1.00,
                     0b1111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111,    'csBGA'),


            
       #         15 x 15     
            BgaConfig( 225,  15,    15,  0.40,  0.25,  7.00,   7.00,  1.00,
                       0b111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111,  'ucBGA'),

       #         16 x 16     
            
            BgaConfig( 208,  16,    16,  1.00,  0.50,  17.0,   17.0,  1.40,
                       0b1111111111111111111111111111111111111111111111111111111111111111111100000000111111110000000011111111001111001111111100111100111111110011110011111111001111001111111100000000111111110000000011111111111111111111111111111111111111111111111111111111111111111111,  'ftBGA'),

        
            BgaConfig( 208,  16,    16,  1.00,  0.60,  17.0,   17.0,  1.70,

        0b1111111111111111111111111111111111111111111111111111111111111111111100000000111111110000000011111111001111001111111100111100111111110011110011111111001111001111111100000000111111110000000011111111111111111111111111111111111111111111111111111111111111111111,  'fpBGA'),

           BgaConfig( 237,  16,    16,  1.00,  0.50,  17.0,  17.0,   1.55,
            0b1111111111111111111011111111111111101111111111111110111111111111111011111111111111101110111111111110110011111111111011001111111111101100111111111110110011111111111111101111111111111111111111111111111111111111111111111111111111111111111111111111111111111111, 'ftBGA'),

            
            BgaConfig( 256,  16,    16,  0.80,  0.45,  14.0,  14.0,   1.70,
                       0b1111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111, 'caBGA'),


            BgaConfig( 256,  16,    16,  0.50,  0.30,  9.00,  9.00,   1.00,
                       0b1111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111, 'csfBGA'),


            BgaConfig( 256,  16,    16,  1.00,  0.50,  17.0,  17.0,   1.40,
                       0b1111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111, 'ftBGAopt1'),


                     BgaConfig( 256,  16,    16,  1.00,  0.60,  17.0,  17.0,   1.70,
                       0b1111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111, 'ftBGAopt2'),



                   BgaConfig( 256,  16,    16,  1.00,  0.50,  17.0,  17.0,   1.55,
                       0b1111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111, 'ftBGAopt3'),

            



            
       #         18 x 18     
            
            BgaConfig( 324,  18,    18,  0.80,  0.45,  15.0,   15.0,  1.70,
                        0b111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111,    'caBGA'),



            BgaConfig( 324,  18,    18,  0.50,  0.30,  10.0,   10.0,  1.00,
                        0b111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111,    'csfBGA'),



            BgaConfig( 324,  18,    18,  1.00,  0.60,  19.0,   19.0,  1.50,
                        0b111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111,    'ftBGA'),


            
            

            BgaConfig( 285,  18,    18,  0.50,  0.30,  10.0,   10.0,  1.30,
                        0b011111111111111110111111111111111111111111111111111111111000001000000111000011111111110000111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111000011111111110000111101111111101111111101111111101111111101111111101111011101111111101110,   'csfBGA'),

      #         19 x 19

            BgaConfig( 328,  19,    19,  0.50,  0.30,  10.0,   10.0,  1.35,
                    0b1111111111111111111111111111111111111111111111111111111111111111111111111111111101111111110111111110111111111011111111011111111101111111101111111110111111110111111111011111111011111111101111111101111111110111111110111111111011111111011111111101111111101111111110111111110111111111011111111000000000001111111111111111111111111111111111111111111111111111111111111,   'csBGA'),


            


            
       #         20 x 20
            
            BgaConfig( 256,  20,    20,  1.27,  0.75,  27.0,   27.0,  1.70,
                        0b1111111111111111111111111111111111111111111111111111111111111111111111111111111111110000000000001111111100000000000011111111000000000000111111110000000000001111111100000000000011111111000000000000111111110000000000001111111100000000000011111111000000000000111111110000000000001111111100000000000011111111000000000000111111111111111111111111111111111111111111111111111111111111111111111111111111111111,  'SBGA'),


                       
          BgaConfig( 272,  20,    20,  1.27,  0.75,  27.0,   27.0,  2.25,
                     0b1111111111111111111111111111111111111111111111111111111111111111111111111111111111110000000000001111111100000000000011111111000000000000111111110000000000001111111100001111000011111111000011110000111111110000111100001111111100001111000011111111000000000000111111110000000000001111111100000000000011111111000000000000111111111111111111111111111111111111111111111111111111111111111111111111111111111111,  'BGA'),



          BgaConfig( 332,  20,    20,  0.80,  0.45,  17.0,   17.0,  2.00,
                0b1111111111111111111111111111111111111111111111111111111111111111111111111111111111110111111111101111111110000000000111111111100000000001111111111001111110011111111110011111100111111111100111111001111111111001111110011111111110011111100111111111100111111001111111111000000000011111111110000000000111111111011111111110111111111111111111111111111111111111111111111111111111111111111111111111111111111111   ,   'caBGA'),

                     
                     


    
       #         22 x 22                 
            BgaConfig( 284,  22,    22,  0.50,  0.31,  12.0,   12.0,  1.00,
                        0b1111111111111111111111100000000000000000000110111111111111111111011010000000000000000101101011111111111111010110101000000000000101011010101111111111010101101010111111111101010110101011000000110101011010101101111011010101101010110111101101010110101011011110110101011010101101111011010101101010110000001101010110101011111111110101011010101111111111010101101010000000000001010110101111111111111101011010000000000000000101101111111111111111110110000000000000000000011111111111111111111111,     'csBGA')
,

       #         24 x 24     
            BgaConfig( 320,  24,    24,  1.27,  0.75,  31.0,   31.0,  1.70,
                0b111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111100000000000000001111111100000000000000001111111100000000000000001111111100000000000000001111111100000000000000001111111100000000000000001111111100000000000000001111111100000000000000001111111100000000000000001111111100000000000000001111111100000000000000001111111100000000000000001111111100000000000000001111111100000000000000001111111100000000000000001111111100000000000000001111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111,   'SBGA'),




       #         26 x 26     
            BgaConfig( 352,  26,    26,  1.27,  0.75,  33.0,   33.0,  1.70,
                0b1111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111110000000000000000001111111100000000000000000011111111000000000000000000111111110000000000000000001111111100000000000000000011111111000000000000000000111111110000000000000000001111111100000000000000000011111111000000000000000000111111110000000000000000001111111100000000000000000011111111000000000000000000111111110000000000000000001111111100000000000000000011111111000000000000000000111111110000000000000000001111111100000000000000000011111111000000000000000000111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111       ,   'SBGA'),



            






            

            

            
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
