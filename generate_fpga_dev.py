
# importing csv module 
import csv 
import sys
import argparse

parser = argparse.ArgumentParser(description='create a fpga from csv file')
parser.add_argument("--design")
parser.add_argument("--group")
parser.add_argument("--file")
parser.add_argument("--package")
args = parser.parse_args()
design_name = args.design
group_name = args.group
file_name = args.file
package = args.package


# initializing 

cvs_raw_data = []
uuid_pads = [] 
uuid_signals = []


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

generator = 'librepcb-parts-generator (generate_fpga_dev.py)'

# Initialize UUID cache
uuid_cache_file = 'uuid_cache_{}_pkg.csv'.format(group_name)
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



def generate_dev(
    cvs_file: str, 
    dirpath: str,
    author: str,
    name: str,
    kind: str,
    cmpcat: str,
    keywords: str,
    default_value: str,
    version: str,
    create_date: Optional[str],
) -> None:
    category      = 'dev'

    with open(cvs_file, 'r') as CSVxfile: 
          # creating a csv reader object 
          CSVxreader = csv.reader(CSVxfile)  
          # extracting each data row one by one 
          for row in CSVxreader:
               cvs_raw_data.append(row) 
               
          print("Total no. of pins: %d"%(CSVxreader.line_num))
          num_of_rows = CSVxreader.line_num



          
    pad_list =[]
    pad_name =[]
    lines = []
    num_of_pins = 0

    for row in cvs_raw_data[:num_of_rows]: 
      # parsing each column of a row

      if row[0] == "FOOT":  package = row[1]
        
      if row[0] == "PIN":  
        pad_name.append(row[1])
        pad_list.append(row[3])
        uuid_pads.append(uuid('pkg', package,'pad-{}'.format(row[3]))) 
        uuid_signals.append(uuid('cmp', kind, 'signal-{}_{}'.format(row[1],row[3])) )
        print(' {} {} {} {} '.format(row[1],row[3],uuid('cmp', kind, 'signal-{}_{}'.format(row[1],row[3])),uuid('pkg', package,'pad-{}'.format(row[3]))  ))
        num_of_pins = num_of_pins +1
        
    print("device: %s   %s  %s"%(design_name, file_name, package ))    
        
    for p in range(1, num_of_pins + 1):
       print(' {} {} {}  '.format(p ,uuid_signals[p-1],uuid_pads[p-1]))

      
    uuid_dev = uuid('dev', kind, 'dev')
    uuid_cmp = uuid('cmp', kind, 'cmp')
    uuid_pkg = uuid('pkg', package, 'pkg')
      
    # General info

    lines.append('(librepcb_device {}'.format(uuid_dev))
    lines.append(' (name "{}")'.format(name))
    lines.append(' (description "A  '
                   'Generated with {}")'.format(generator))
    lines.append(' (keywords "{}")'.format(keywords))
    lines.append(' (author "{}")'.format(author))
    lines.append(' (version "0.1")')
    lines.append(' (created {})'.format(create_date or now()))
    lines.append(' (deprecated false)')
    lines.append(' (category {})'.format(cmpcat))
    lines.append(' (component {})'.format(uuid_cmp))
    lines.append(' (package {})'.format(uuid_pkg))
    signalmappings = []



    for p in range(1, num_of_pins + 1):
                signalmappings.append(' (pad {} (signal {}))'.format(uuid_pads[p - 1], uuid_signals[p - 1]))
    lines.extend(sorted(signalmappings))
    lines.append(')')

    for p in range(1, num_of_pins + 1):
       print(' {} {} {}  '.format(p ,uuid_signals[p-1],uuid_pads[p-1]))

    
    dev_dir_path = path.join(dirpath, uuid_dev)
    if not (path.exists(dev_dir_path) and path.isdir(dev_dir_path)):
               makedirs(dev_dir_path)
    with open(path.join(dev_dir_path, '.librepcb-dev'), 'w') as f:
                f.write('0.1\n')
    with open(path.join(dev_dir_path, 'device.lp'), 'w') as f:
               f.write('\n'.join(lines))
               f.write('\n')

    print(' {}'.format(uuid_dev))







            
if __name__ == '__main__':
    def _make(dirpath: str) -> None:
        if not (path.exists(dirpath) and path.isdir(dirpath)):
            makedirs(dirpath)
    _make('out')
    _make('out/{}'.format(group_name))
    _make('out/{}/dev'.format(group_name))


    
    generate_dev(
        cvs_file=file_name,
        dirpath='out/{}/dev'.format(group_name),
        author='John E.',
        name=design_name,
        kind=design_name,
        cmpcat='c3dfb625-e6e4-46c1-a1df-d14eeecfc965',
        keywords='Fpga',
        default_value='{{PARTNUMBER}}',
        version='0.1',
        create_date='2019-12-17T00:00:00Z',
    )

    save_cache(uuid_cache_file, uuid_cache)
