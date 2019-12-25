
# importing csv module 
import csv 
import sys
import argparse

parser = argparse.ArgumentParser(description='create a fpga from csv file')
parser.add_argument("--design")
parser.add_argument("--group")
parser.add_argument("--directory")
args = parser.parse_args()
design_name = args.design
group_name = args.group
directory_name = args.directory

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

generator = 'librepcb-parts-generator (generate_fpga_cmp.py)'

# Initialize UUID cache
uuid_cache_file = 'uuid_cache_{}.csv'.format(group_name)
uuid_cache = init_cache(uuid_cache_file)


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



def generate_cmp(
    cvs_file: str, 
    dirpath: str,
    author: str,
    name: str,
    kind: str,
    cmpcat: str,
    default_value: str,
    create_date: Optional[str],
) -> None:
    category      = 'cmp'
    version       = '0.1'
    keywords      = '   '

    with open(cvs_file, 'r') as CSVxfile: 
          # creating a csv reader object 
          CSVxreader = csv.reader(CSVxfile)  
          # extracting each data row one by one 
          for row in CSVxreader:
               cvs_raw_data.append(row) 
               

          num_of_rows = CSVxreader.line_num

    pad_list =[]
    pad_name =[]
    uuid_pins =[]
    uuid_signals =[]
    num_of_pins  = 0
    for row in cvs_raw_data[:num_of_rows]: 
      # parsing each column of a row
      row_type =row[0]

      if row_type == "VERSION" :        version =row[1]
      if row_type == "KEYWORDS" :       keywords =row[1]

        

      if row_type == "PIN":  
          pad_name.append(row[1])
          pad_list.append(row[3])
          uuid_pins.append(uuid('sym', kind,'pin-{}_{}'.format(row[1],row[3])))
          uuid_signals.append(uuid('cmp', kind,'signal-{}_{}'.format(row[1],row[3])))
          num_of_pins = num_of_pins + 1

      
      
    def _uuid(identifier: str) -> str:
            return uuid(category, kind, identifier)


          




    uuid_cmp = _uuid('cmp')
    uuid_variant = _uuid('variant-default')
    uuid_gate = _uuid('gate-default')
    uuid_symbol = uuid('sym', kind, 'sym')
    uuid_dev =   uuid('dev', kind, 'dev')





    
    # General info
    component = Component(
            uuid_cmp,
            Name('{}'.format(name)),
            Description('created from file---  {}.\\n'
                        'Generated with {}'.format(cvs_file, generator)),
            Keywords('{}'.format( keywords)),
            Author(author),
            Version(version),
            Created(create_date or now()),
            Deprecated(False),
            Category(cmpcat),
            SchematicOnly(False),
            DefaultValue(default_value),
            Prefix('U'),
        )


    for p in range(1, num_of_pins + 1):
            component.add_signal(Signal(
                uuid_signals[p-1 ],
                Name('{}_{}'.format(pad_name[p-1],pad_list[p-1])),
                Role.PASSIVE,
                Required(False),
                Negated(False),
                Clock(False),
                ForcedNet(''),
            ))

    gate = Gate(
            uuid_gate,
            SymbolUUID(uuid_symbol),
            Position(0.0, 0.0),
            Rotation(0.0),
            Required(True),
            Suffix(''),
        )
    for p in range(1, num_of_pins+ 1):
            gate.add_pin_signal_map(PinSignalMap(
                uuid_pins[p - 1],
                SignalUUID(uuid_signals[p - 1]),
                TextDesignator.SYMBOL_PIN_NAME,
            ))







            
    component.add_variant(Variant(uuid_variant, Norm.EMPTY, Name('default'), Description(''), gate))

    component.serialize(dirpath)
      
    cmp_dir_path = path.join(dirpath, uuid_cmp)
    if not (path.exists(cmp_dir_path) and path.isdir(cmp_dir_path)):
            makedirs(cmp_dir_path)
    with open(path.join(cmp_dir_path, '.librepcb-cmp'), 'w') as f:
            f.write('0.1\n')
    with open(path.join(cmp_dir_path, 'component.lp'), 'w') as f:
            f.write(str(component))
            f.write('\n')

    print(': Wrote component {}'.format( uuid_cmp))

            
if __name__ == '__main__':
    def _make(dirpath: str) -> None:
        if not (path.exists(dirpath) and path.isdir(dirpath)):
            makedirs(dirpath)
    _make('out')
    _make('out/{}'.format(group_name))
    _make('out/{}/cmp'.format(group_name))


    
    generate_cmp(
        cvs_file='{}{}.csv'.format(directory_name,design_name),
        dirpath='out/{}/cmp'.format(group_name),
        author='John E.',
        name=design_name,
        kind=design_name,
        cmpcat='c3dfb625-e6e4-46c1-a1df-d14eeecfc965',
        default_value='{{PARTNUMBER}}',
        create_date='2019-12-17T00:00:00Z',
    )

    save_cache(uuid_cache_file, uuid_cache)
