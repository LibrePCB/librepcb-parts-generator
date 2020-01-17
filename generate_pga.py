"""
Generate the following  packages:

- PGA ( JEDEC )


"""
from os import makedirs, path
from uuid import uuid4

from typing import Dict, Iterable, List, Optional

from common import format_float as ff
from common import format_ipc_dimension as fd
from common import generate_courtyard, indent, init_cache, now, save_cache

generator = 'librepcb-parts-generator (generate_pga.py)'

line_width        = 0.25  #
pkg_text_height   = 1.0   #
silkscreen_offset = 0.8   #
silkscreen_pin_1  = 2.4   #
courtyard_excess  = 0.5   #
label_offset      = 1.27  #

# Initialize UUID cache
uuid_cache_file = 'uuid_cache_pga.csv'
uuid_cache = init_cache(uuid_cache_file)


def uuid(category: str, full_name: str, identifier: str) -> str:
    """
    Return a uuid for the specified pin.

    Params:
        category:
            For example 'cmp' or 'pkg'.
        full_name:
            For example "PGA".
        identifier:
            For example 'pad-1' or 'pin-13'.
    """
    key = '{}-{}-{}'.format(category, full_name, identifier).lower().replace(' ', '~')
    if key not in uuid_cache:
        uuid_cache[key] = str(uuid4())
    return uuid_cache[key]





class PgaConfig:
    def __init__(
        self,
        pin_count: int,
        row_count: int,
        col_count: int,
        pitch: float,
        pad_width: float,
        hole_size: float,
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
        self.pad_width = pad_width
        self.hole_size = hole_size
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
    configs: Iterable[PgaConfig],
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
        hole_size = config.hole_size
        body_width = config.body_width
        body_length = config.body_length
        pad_width = config.pad_width
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
            hole_size=fd(hole_size),
            pad_width=fd(pad_width),
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
            hole_size=hole_size,
            pad_width=pad_width,
            mask=mask,
            variation=config.variation,
        )

        def _uuid(identifier: str) -> str:
            return uuid(category, full_name, identifier)

        uuid_pkg = _uuid('pkg')
        uuid_pads = []

        print('Generating {}: {}'.format(full_name, uuid_pkg))
        print('    Pin Count: {}'.format(pin_count))
        print('   row_count : {}'.format(row_count))
        print('   col_count : {}'.format(col_count))
        print('       pitch : {}'.format(pitch))
        print('  body_width : {}'.format(body_width))
        print(' body_length : {}'.format(body_length))
        print('   hole_size : {}'.format(hole_size))
        print('   pad_width : {}'.format(pad_width))
        print('   variation : {}'.format(config.variation))

                
        
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
                lines.append('  (pad {} (side tht) (shape round)'.format(pad_uuid))
                lines.append('   (position {} {}) (rotation 0.0) (size {} {}) (drill {})'.format(
                    pxo, ff(y), ff(pad_width), ff(pad_width), ff(hole_size),
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


    # PGA

    _make('out/pga/pkg')
    generate_pkg(
        dirpath='out/pga/pkg',
        author='John E.',
        # Name according to IPC7351C
        name='PGA{pin_count}P{pitch}C{col_count}R{row_count}L{body_length}X{body_width}H{height}B',
        description='{pin_count}-pin Pin Grid Array  (PGA), '
                    'standardized by JEDEC (), variation {variation}.\\n\\n'
                    'Pitch: {pitch:.2f} mm\\nBody length: {body_length:.2f} mm\\n'
                    'Body width: {body_width:.2f} mm\\n'
                    'Height: {height:.2f} mm\\n'
                    'Pad width: {pad_width:.2f} mm',
        configs=[
#  IPC-7251  Naming Convention fo Through-Hole Land Patterns  Pin Grid Array’s
#  PGA + Pin Qty + P Pitch + C Pin Columns + R Pin Rows + L Body Length X Body Width + H Component Height
#
#  Example: PGA 84 P254 C10 R10 L2500 X2500 H300 B
#  Pin Grid Array: Pin Qty 84; Pin Pitch 2.54; Columns 10; Rows 10; Body Length 25.00 X 25.00; Component Height 3.00 B ?????           
#               pin   row    col   pitch   pad     hole         body     body    height    mask                variation
#              count  count count   mm    width    size         width   length    mm
#                                           mm      mm           mm       mm         
#  11 x 11
   PgaConfig(  68,   11,   11,    2.54,  1.6,     .8,          28.19,    28.19, 4.17,
               0b0111111111011111111111110000000111100000001111000000011110000000111100000001111000000011110000001111111111111101111111110              ,  'G-68' ), #

#  13 x 13
   PgaConfig(  100,   13,   13,    2.54,  1.6,     .8,          34.09,    34.09, 4.29,
               0b1111111111111111111111111111000111000111100000000011110000000001111100000001111110000000111111000000011111000000000111100000000011110001110011111111111111111111111111111 ,'G-100' ), #  
            
#  14 x 14
   PgaConfig(  133,   14,   14,    2.54,  1.6,     .8,          37.6,    37.6, 3.68,
               0b1111111111111111111111111111111111111111111110000000011111100000000111111000000001111110000000011111100000000111111000000001111110000000011111100000001111111111111111111111111111111111111111111111   ,  'CPGA' ), #  PGA133P254C14R14L3760X3760H368B

            

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
        pkgcat='5bc3a6c4-2f77-4a9e-85ca-e261f4757312',
        keywords='pga, package,smd,jedec,MO',
        version='0.1',
        create_date='2020-01-16T12:00:00Z',
    )
    save_cache(uuid_cache_file, uuid_cache)
