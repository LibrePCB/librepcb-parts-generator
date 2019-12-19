
# importing csv module 
import csv 
import sys
import argparse

parser = argparse.ArgumentParser(description='create a fpga from csv file')
parser.add_argument("--design")
parser.add_argument("--file")
args = parser.parse_args()
design_name = args.design
file_name = args.file

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

generator = 'librepcb-parts-generator (generate_fpga_sym.py)'

width = 2.54
line_width = 0.25
pkg_text_height = 1.0
sym_text_height = 2.54


# Initialize UUID cache
uuid_cache_file = 'uuid_cache_fpgas.csv'
uuid_cache = init_cache(uuid_cache_file)


def uuid(category: str, kind: str, variant: str, identifier: str) -> str:
    """
    Return a uuid for the specified pin.

    Params:
        category:
            For example 'cmp' or 'pkg'.
        kind:
            For example 'pinheader' or 'pinsocket'.
        variant:
            For example '1x5-D1.1' or '1x13'.
        identifier:
            For example 'pad-1' or 'pin-13'.
    """
    key = '{}-{}-{}-{}'.format(category, kind, variant, identifier).lower().replace(' ', '~')
    if key not in uuid_cache:
        uuid_cache[key] = str(uuid4())
    return uuid_cache[key]



def generate_sym(
    cvs_file: str, 
    dirpath: str,
    author: str,
    name: str,
    name_lower: str,
    kind: str,
    cmpcat: str,
    keywords: str,
    version: str,
    create_date: Optional[str],
) -> None:
    category      = 'sym'
    top_count     = 12
    bottom_count  = 12
    left_count    =  6
    right_count   =  6
    real_width    =  6
    real_height   =  6


    with open(cvs_file, 'r') as CSVxfile: 
          # creating a csv reader object 
          CSVxreader = csv.reader(CSVxfile)  
          # extracting each data row one by one 
          for row in CSVxreader:
               cvs_raw_data.append(row) 
               
               
          print("Total no. of pins: %d"%(CSVxreader.line_num))
          num_of_pins = CSVxreader.line_num

    pad_list =[]
    for row in cvs_raw_data[:num_of_pins]: 
      # parsing each column of a row
      pin_type =row[1]
      if pin_type == "L" :left_count = left_count +1
      if pin_type == "R" :right_count = right_count +1
      if pin_type == "T" :top_count = top_count +2
      if pin_type == "B" :bottom_count = bottom_count +2
      pad_list.append(row[2])

      


    if top_count >= bottom_count : real_width = top_count
    if left_count >= right_count : real_height = left_count
    if top_count <= bottom_count : real_width = bottom_count
    if left_count <= right_count : real_height = right_count


    print("%10s Top   "%top_count)
    print("%10s Bottom"%bottom_count)
    print("%10s Left  "%left_count)
    print("%10s Right "%right_count)        
    print("Width    : %d"%real_width)
    print("Height   : %d"%real_height)
    



    def _uuid(identifier: str) -> str:
            return uuid(category, kind, variant, identifier)

    variant = '--'
          

    for i in range(1, num_of_pins + 1, 1):
        uuid_pins = [_uuid('pin-{}'.format(pad_list[p])) for p in range(i)]

    uuid_sym = _uuid('sym')
    uuid_polygon = _uuid('polygon-contour')
    uuid_decoration = _uuid('polygon-decoration')
    uuid_text_name = _uuid('text-name')
    uuid_text_value = _uuid('text-value')

    # General info
    symbol = Symbol(
            uuid_sym,
            Name('{}'.format(name)),
            Description('created from file---  {}.\\n'
                        'Generated with {}'.format(cvs_file, generator)),
            Keywords('{}'.format( keywords)),
            Author(author),
            Version(version),
            Created(create_date or now()),
            Category(cmpcat),
        )


        



    
    p          = 1
    y_max      =  round(real_height/2) * width 
    y_min      = -round(real_height/2) * width
    w          =  real_width/2 *width
    x_min      = -real_width/2 *width -width
    x_max      = real_width/2 *width  +width
    left_pin   = y_max -width*2
    right_pin  = y_max -width*2
    top_pin    = w -width*2
    bottom_pin = w -width*2
    
    for row in cvs_raw_data[:CSVxreader.line_num]: 
      # parsing each column of a row
      pin_type =row[1]
      pin_name =row[0]
      pin_number =row[2]
      if pin_type == "L" :      pin = SymbolPin(
                            uuid_pins[p - 1],
                            Name(row[0]),
                            Position((x_min) , left_pin),
                            Rotation(0.0),
                            Length(width)
                            )

      if pin_type == "R" :      pin = SymbolPin(
                            uuid_pins[p - 1],
                            Name(row[0]),
                            Position((x_max) , right_pin),
                            Rotation(180.0),
                            Length(width)
                            )

      if pin_type == "T" :      pin = SymbolPin(
                            uuid_pins[p - 1],
                            Name(row[0]),
                            Position((top_pin) , y_max+ width),
                            Rotation(270.0),
                            Length(width)
                            )


      if pin_type == "B" :      pin = SymbolPin(
                            uuid_pins[p - 1],
                            Name(row[0]),
                            Position((bottom_pin) , y_min - width),
                            Rotation(90.0),
                            Length(width)
                            )

      

      
                            
      if pin_type == "L" :      left_pin =  left_pin -width

      if pin_type == "R" :      right_pin =  right_pin -width

      if pin_type == "T" :      top_pin =  top_pin -width

      if pin_type == "B" :      bottom_pin =  bottom_pin -width            
                            
      p = p +1
      symbol.add_pin(pin)


            
    # Polygons


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

    print(' {}: Wrote symbol {}'.format( kind, uuid_sym))

            
if __name__ == '__main__':
    def _make(dirpath: str) -> None:
        if not (path.exists(dirpath) and path.isdir(dirpath)):
            makedirs(dirpath)
    _make('out')
    _make('out/fpgas')
    _make('out/fpgas/sym')

    generate_sym(
        cvs_file=file_name,
        dirpath='out/fpgas/sym',
        author='John E.',
        name=design_name,
        name_lower='fpga',
        kind=design_name,
        cmpcat='c3dfb625-e6e4-46c1-a1df-d14eeecfc965',
        keywords='Fpga',
        version='0.1',
        create_date='2019-12-17T00:00:00Z',
    )

    save_cache(uuid_cache_file, uuid_cache)