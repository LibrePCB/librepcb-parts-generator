
# importing csv module 
import csv 
import sys
import argparse

parser = argparse.ArgumentParser(description='create a device from csv file')
parser.add_argument("--design")
parser.add_argument("--group")
parser.add_argument("--directory")
args = parser.parse_args()
design_name = args.design
group_name = args.group
directory_name = args.directory


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

generator = 'librepcb-parts-generator (generate_dev.py)'



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

# Initialize cmpcat UUID 
uuid_cmpcat_file = 'uuid_cache_{}_cmpcat.csv'.format(group_name)
uuid_cache = init_cache(uuid_cmpcat_file)
cmpcat = uuid('cmpcat',design_name,"cmpcat")
save_cache(uuid_cmpcat_file, uuid_cache)


# Initialize UUID cache
uuid_cache_file = 'uuid_cache_{}_pkg.csv'.format(group_name)
uuid_cache = init_cache(uuid_cache_file)




def generate_dev(
    cvs_file: str, 
    dirpath: str,
    author: str,
    name: str,
    cmpcat: str,
    create_date: Optional[str],
) -> None:
    category      = 'dev'
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
    lines = []
    num_of_pins = 0
    package = "none"
    
    for row in cvs_raw_data[:num_of_rows]: 
      # parsing each column of a row
      row_type =row[0]

      if row_type == "VERSION" :        version =row[1]
      if row_type == "KEYWORDS" :       keywords =row[1]

      if row_type == "FOOT":  package = row[1]
        
      if row_type == "PIN":  
        pad_name.append(row[1])
        pad_list.append(row[3])
        uuid_pads.append(uuid('pkg', package,'pad-{}'.format(row[3]))) 
        uuid_signals.append(uuid('cmp', name, 'signal-{}_{}'.format(row[1],row[3])) )
        num_of_pins = num_of_pins +1
        
    print("                          device: %s Number of pins %s"%(design_name,num_of_pins ))    
        


      
    uuid_dev = uuid('dev', name, 'dev')
    uuid_cmp = uuid('cmp', name, 'cmp')
    uuid_pkg = uuid('pkg', package, 'pkg')
      
    # General info

    lines.append('(librepcb_device {}'.format(uuid_dev))
    lines.append(' (name "{}")'.format(name))
    lines.append(' (description "  '
                   'Generated with {}")'.format(generator))
    lines.append(' (keywords "{}")'.format(keywords))
    lines.append(' (author "{}")'.format(author))
    lines.append(' (version "{}")'.format(version))
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

    if package != "none":    
      dev_dir_path = path.join(dirpath, uuid_dev)
      if not (path.exists(dev_dir_path) and path.isdir(dev_dir_path)):
                 makedirs(dev_dir_path)
      with open(path.join(dev_dir_path, '.librepcb-dev'), 'w') as f:
                  f.write('0.1\n')
      with open(path.join(dev_dir_path, 'device.lp'), 'w') as f:
                 f.write('\n'.join(lines))
                 f.write('\n')

      print('                           {}'.format(uuid_dev))







            
if __name__ == '__main__':
    def _make(dirpath: str) -> None:
        if not (path.exists(dirpath) and path.isdir(dirpath)):
            makedirs(dirpath)
    _make('out')
    _make('out/{}'.format(group_name))
    _make('out/{}/dev'.format(group_name))


    
    generate_dev(
        cvs_file='{}{}.csv'.format(directory_name,design_name),
        dirpath='out/{}/dev'.format(group_name),
        author='John E.',
        name=design_name,
        cmpcat=cmpcat,
        create_date='2019-12-17T00:00:00Z',
    )


