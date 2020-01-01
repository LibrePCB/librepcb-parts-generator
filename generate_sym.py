
# importing csv module 
import csv 
import sys
import argparse

parser = argparse.ArgumentParser(description='create a symbol from csv file')
parser.add_argument("--design")
parser.add_argument("--variant")
parser.add_argument("--group")
parser.add_argument("--directory")
parser.add_argument("--part")

args = parser.parse_args()
design_name = args.design
variant_name = args.variant
group_name = args.group
directory_name = args.directory
part_name = args.part

# initializing 

cvs_raw_data = [] 



"""

"""
from os import makedirs, path
from uuid import uuid4

from typing import Callable, Iterable, List, Optional, Tuple

from common import format_float as ff
from common import init_cache, now, save_cache
from entities.common import (
    Align, Angle, Author, Category, Created, Deprecated, Description, Fill, GrabArea, Height, Keywords, Layer, Length,
    Name, Polygon, Position, Rotation, Text, Value, Version, Vertex, Width
)
from entities.component import (
    Clock, Component, DefaultValue, ForcedNet, Gate, Negated, Norm, PinSignalMap, Prefix, Required, Role, SchematicOnly,
    Signal, SignalUUID, Suffix, SymbolUUID, TextDesignator, Variant
)
from entities.symbol import Pin as SymbolPin
from entities.symbol import Symbol

generator = 'librepcb-parts-generator (generate_sym.py)'

width = 2.54
line_width = 0.25
pkg_text_height = 1.0
sym_text_height = 2.54


part = float(part_name)

if part >= 1 :
   design_name = '{}_{}'.format(design_name,part_name)



def uuid(category: str, kind: str, identifier: str) -> str:
    """
    Return a uuid for the specified pin.

    Params:
        category:
            For example 'cmp' or 'pkg'.
        kind:
            For example 'pinheader' or 'pinsocket'.
        identifier:
            For example 'pad-1' or 'pin-13'.
    """
    key = '{}-{}-{}'.format(category, kind, identifier).lower().replace(' ', '~')
    if key not in uuid_cache:
        uuid_cache[key] = str(uuid4())
    return uuid_cache[key]


uuid_cmpcat_file = 'uuid_cache_{}_cmpcat.csv'.format(group_name)
uuid_cache = init_cache(uuid_cmpcat_file)
cmpcat = uuid('cmpcat',design_name,"cmpcat")
save_cache(uuid_cmpcat_file, uuid_cache)



# Initialize UUID cache
uuid_cache_file = 'uuid_cache_{}.csv'.format(group_name)
uuid_cache = init_cache(uuid_cache_file)






def generate_sym(
    cvs_file: str, 
    dirpath: str,
    author: str,
    name: str,
    variant: str,
    cmpcat: str,
    create_date: Optional[str],
) -> None:
    category      = 'sym'
    top_count     = 12
    bottom_count  = 12
    left_length   =  0
    right_length  =  0
    left_count    =  6
    right_count   =  6
    real_width    =  6
    real_height   =  6
    version       = '0.1'
    keywords      = '   '


    with open(cvs_file, 'r') as CSVxfile: 
          # creating a csv reader object 
          CSVxreader = csv.reader(CSVxfile)  
          # extracting each data row one by one 
          for row in CSVxreader:
               cvs_raw_data.append(row) 
               
               
          print("Total no. of rows: %d"%(CSVxreader.line_num))
          num_of_rows = CSVxreader.line_num

    pad_list  = []
    pad_type  = []
    pad_name  = []
    pad_posx  = []
    pad_posy  = []
    PAD_posx  = []
    PAD_posy  = []
    pad_length  = []
    pad_orientation  = []
    uuid_pins = []
    num_of_pins = 0
    low_x  = 0
    low_y  = 0
    high_x  = 0
    high_y  = 0


    for row in cvs_raw_data[:num_of_rows]: 
      # parsing each column of a row
      row_type =row[0]


      if row_type == "VERSION" :        version =row[1]
      if row_type == "KEYWORDS" :       keywords =row[1]

      if row_type == "RECT" :
           low_x  =float(row[1])
           low_y  =float(row[2])
           high_x =float(row[3])
           high_y =float(row[4])



           

      if row_type == "PIN" :
        pin_type =row[2]
        if pin_type == "R" :
            left_count   = left_count   +1
            left_length = max(round(len(row[1])/5),left_length)
            pad_orientation.append(0.0)
            
        if pin_type == "L" :
            right_count  = right_count  +1
            right_length = max(round(len(row[1])/5),right_length)
            pad_orientation.append(180.0)
        if pin_type == "D" :
            top_count    = top_count    +1
            pad_orientation.append(270.0)
            
        if pin_type == "U" :
            bottom_count = bottom_count +1
            pad_orientation.append(90.0)
            
        pad_name.append(row[1])
        pad_type.append(row[2])
        pad_list.append(row[3])
        if variant != "default" :   
          pad_posx.append(float(row[4])/39.3701)
          pad_posy.append(float(row[5])/39.3701)
          pad_length.append(float(row[6])/39.3701)
          
        if variant == "default" :   
          pad_posx.append(0)
          pad_posy.append(0)
          pad_length.append(width)




        uuid_pins.append(uuid('sym',name,'pin-{}_{}'.format(row[1],row[3])))
        num_of_pins = num_of_pins +1


    real_width = max(top_count,bottom_count) + left_length +  right_length
    real_height = max(left_count,right_count)



    print("%10s Top   "%top_count)
    print("%10s Bottom"%bottom_count)
    print("%10s Left  "%left_count)
    print("%10s Right "%right_count)        
    print("Width    : %d"%real_width)
    print("Height   : %d"%real_height)
    



    def _uuid(identifier: str) -> str:
            return uuid(category, name, identifier)

          



    uuid_sym = uuid('sym', '{}_{}'.format(name, variant),'sym')
    uuid_polygon = _uuid('polygon-contour')
    uuid_decoration = _uuid('polygon-decoration')
    uuid_text_name = _uuid('text-name')
    uuid_text_value = _uuid('text-value')



    y_max      =  round(real_height/2) * width 
    y_min      = -round(real_height/2) * width
    w          =  round(real_width/2+.5) *width
    x_min      = -round(real_width/2+.5) *width 
    x_max      =  round(real_width/2+.5) *width  
    left_pin   = y_max -width*2
    right_pin  = y_max -width*2
    top_pin    = w -width*6
    bottom_pin = w -width*4


    
    for p in range(1, num_of_pins + 1, 1):

      print('Sym   {} {} {} {} '.format(pad_name[p-1],pad_list[p-1],  pad_posx[p-1],pad_posy[p-1] ))

      if variant == "default" :   
      
        # parsing each column of a row
        pin_type =pad_type[p-1]
        if pin_type == "R" :
                            pad_posx[p-1] =  x_min-width
                            pad_posy[p-1] =  left_pin
                            left_pin      =  left_pin -width

        if pin_type == "L" :
                            pad_posx[p-1] =  x_max+width
                            pad_posy[p-1] =  right_pin
                            right_pin =  right_pin -width

        if pin_type == "D" :
                            pad_posx[p-1] =  top_pin
                            pad_posy[p-1] =  y_max+ width
                            top_pin =  top_pin -width


        if pin_type == "U" :
                            pad_posx[p-1] =  bottom_pin
                            pad_posy[p-1] =  y_min - width
                            bottom_pin =  bottom_pin -width            




         
    # General info
    symbol = Symbol(
            uuid_sym,
            Name('{}'.format(name)),
            Description('created from file---  {}.\\nVariant-{}\\n'
                        'Generated with {}'.format(cvs_file,variant, generator)),
            Keywords('{}'.format( keywords)),
            Author(author),
            Version(version),
            Created(create_date or now()),
            Category(cmpcat),
        )    



    for p in range(1, num_of_pins + 1, 1):
      # parsing each column of a row
      pin_type   = pad_type[p-1]
      pin_name   = pad_name[p-1]
      pin_posx   = pad_posx[p-1]
      pin_posy   = pad_posy[p-1]
      pin_length = pad_length[p-1]
      pin_orient = pad_orientation[p-1]
      

      pin = SymbolPin(
                     uuid_pins[p - 1],
                     Name( pin_name),
                     Position(pin_posx , pin_posy),
                     Rotation(pin_orient),
                     Length(pin_length)
                     )


      symbol.add_pin(pin)


            
    # Polygons
    if variant == "default" :   

        print("Polygon  %d  %d   "%(y_max,w))
        polygon = Polygon(
             uuid_polygon,
             Layer('sym_outlines'),
             Width(line_width),
             Fill(False),
             GrabArea(True)
            )
        polygon.add_vertex(Vertex(Position(-w, y_max), Angle(0.0)))
        polygon.add_vertex(Vertex(Position(w, y_max), Angle(0.0)))
        polygon.add_vertex(Vertex(Position(w, y_min), Angle(0.0)))
        polygon.add_vertex(Vertex(Position(-w, y_min), Angle(0.0)))
        polygon.add_vertex(Vertex(Position(-w, y_max), Angle(0.0)))
        symbol.add_polygon(polygon)




    if variant != "default" :   


        polygon = Polygon(
             uuid_polygon,
             Layer('sym_outlines'),
             Width(line_width),
             Fill(False),
             GrabArea(True)
            )
        polygon.add_vertex(Vertex(Position(low_x, high_y), Angle(0.0)))
        polygon.add_vertex(Vertex(Position(high_x, high_y), Angle(0.0)))
        polygon.add_vertex(Vertex(Position(high_x, low_y), Angle(0.0)))
        polygon.add_vertex(Vertex(Position(low_x, low_y), Angle(0.0)))
        polygon.add_vertex(Vertex(Position(low_x, high_y), Angle(0.0)))
        symbol.add_polygon(polygon)




        


        

    # Text

    text = Text(uuid_text_name, Layer('sym_names'), Value('{{NAME}}'), Align('center bottom'), Height(sym_text_height), Position(-w+2*width, y_max), Rotation(0.0))
    symbol.add_text(text)

    text = Text(uuid_text_value, Layer('sym_values'), Value('{{VALUE}}'), Align('center top'), Height(sym_text_height), Position(-w+2*width, y_min), Rotation(0.0))
    symbol.add_text(text)

    sym_dir_path = path.join(dirpath, uuid_sym)
    if not (path.exists(sym_dir_path) and path.isdir(sym_dir_path)):
            makedirs(sym_dir_path)
    with open(path.join(sym_dir_path, '.librepcb-sym'), 'w') as f:
            f.write('0.1\n')
    with open(path.join(sym_dir_path, 'symbol.lp'), 'w') as f:
            f.write(str(symbol))
            f.write('\n')

    print(' {}: Wrote symbol {}'.format( name, uuid_sym))

            
if __name__ == '__main__':
    def _make(dirpath: str) -> None:
        if not (path.exists(dirpath) and path.isdir(dirpath)):
            makedirs(dirpath)
    _make('out')
    _make('out/{}'.format(group_name))
    _make('out/{}/sym'.format(group_name))


    generate_sym(
        cvs_file='{}{}.csv'.format(directory_name,design_name),
        dirpath='out/{}/sym'.format(group_name),
        author='John E.',
        name=design_name,
        variant=variant_name,
        cmpcat=cmpcat,
        create_date='2019-12-17T00:00:00Z',
    )

    save_cache(uuid_cache_file, uuid_cache)
