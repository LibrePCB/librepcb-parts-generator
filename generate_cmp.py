
# importing csv module 
import csv 
import sys
import argparse

parser = argparse.ArgumentParser(description='create a component from csv file')
parser.add_argument("--design")
parser.add_argument("--group")
parser.add_argument("--variant")
parser.add_argument("--directory")
args = parser.parse_args()
design_name = args.design
group_name = args.group
variant_name = args.variant
directory_name = args.directory

# initializing 

cvs_raw_data = [] 
boilerplate_raw_data = [] 


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

generator = 'librepcb-parts-generator (generate_cmp.py)'




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














boilerplate_cvs_file='Boilerplate_{}.csv'.format(group_name)






with open(boilerplate_cvs_file, 'r') as CSVBfile: 
          # creating a csv reader object 
          CSVbreader = csv.reader(CSVBfile)  
          # extracting each data row one by one 
          for brow in CSVbreader:
               boilerplate_raw_data.append(brow) 
               
               
          print("                                            Total no. of rows: %d"%(CSVbreader.line_num))
          num_of_brows = CSVbreader.line_num


for brow in boilerplate_raw_data[:num_of_brows]: 
      # parsing each column of a row
      row_type =brow[0]
      if row_type == "CREATE"    :         create_date  =brow[1]
      if row_type == "VERSION"   :         version  =brow[1]
      if row_type == "AUTHOR"    :         author  =brow[1]
      if row_type == "KEYWORDS"  :
          keywords  =brow[1]
          if len(brow) > 2:
            for p in range(2, len(brow)):
                keywords  ='{},{}'.format(keywords,brow[p])


     
print("            Create Date  : {}".format(create_date))
print("            Version  : {}".format(version))
print("            Author   : {}".format(author))
print("            Keywords  : {}".format(keywords))













cvs_file='{}{}.csv'.format(directory_name,design_name)
with open(cvs_file, 'r') as CSVxfile: 
          # creating a csv reader object 
          CSVxreader = csv.reader(CSVxfile)  
          # extracting each data row one by one 
          for row in CSVxreader:
               cvs_raw_data.append(row) 
               

          num_of_rows = CSVxreader.line_num


for row in cvs_raw_data[:num_of_rows]: 
      # parsing each column of a row
      row_type =row[0]

      if row_type == "VERSION" :        version  =row[1]
      if row_type == "KEYWORDS" :       keywords =row[1]
      if row_type == "UNITS" :          units    =row[1]
      if row_type == "DEF"   :          def_name    =row[1]




          



uuid_cmpcat_file = 'uuid_cache_{}_cmpcat.csv'.format(group_name)
uuid_cache = init_cache(uuid_cmpcat_file)
cmpcat = uuid('cmpcat',def_name,"cmpcat")
save_cache(uuid_cmpcat_file, uuid_cache)


# Initialize UUID cache
uuid_cache_file = 'uuid_cache_{}.csv'.format(group_name)
uuid_cache = init_cache(uuid_cache_file)

def generate_cmp(
    cvs_file: str, 
    dirpath: str,
    author: str,
    version: str,
    keywords: str,    
    cmpcat: str,
    default_value: str,
    create_date: Optional[str],
) -> None:
    category      = 'cmp'
    



    
    with open(cvs_file, 'r') as CSVxfile: 
          # creating a csv reader object 
          CSVxreader = csv.reader(CSVxfile)  
          # extracting each data row one by one 
          for row in CSVxreader:
               cvs_raw_data.append(row) 
               

          num_of_rows = CSVxreader.line_num

    pad_list =[]
    pad_name =[]
    pad_unit =[]
    uuid_pins =[]
    uuid_signals =[]
    num_of_pins  = 0
    units        = 0
    for row in cvs_raw_data[:num_of_rows]: 
      # parsing each column of a row
      row_type =row[0]

      if row_type == "VERSION" :        version  =row[1]
      if row_type == "KEYWORDS" :       keywords =row[1]
      if row_type == "UNITS" :          units    =row[1]
      if row_type == "DEF"   :          def_name    =row[1]

        

      if row_type == "PIN":  
          pad_name.append(row[1])
          pad_list.append(row[3])
          uuid_pins.append(uuid('sym', def_name,'pin-{}_{}'.format(row[1],row[3])))
          uuid_signals.append(uuid('cmp', def_name,'signal-{}_{}'.format(row[1],row[3])))
          num_of_pins = num_of_pins + 1
          if units  != 0:  
              pad_unit.append(row[10])
      
    def _uuid(identifier: str) -> str:
            return uuid(category, def_name, identifier)


    print('Number of pins {}'.format(num_of_pins))       




    uuid_cmp = _uuid('cmp')


    uuid_variant_default = _uuid('variant-default')
    uuid_gate_default = _uuid('gate-default')
    uuid_symbol_default = uuid('sym', '{}_default'.format(def_name), 'sym')
    uuid_dev =   uuid('dev', def_name, 'dev')
    
    # General info
    component = Component(
            uuid_cmp,
            Name('{}'.format(def_name)),
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
            uuid_gate_default,
            SymbolUUID(uuid_symbol_default),
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


    variant = Variant(  uuid_variant_default,
                              Norm.EMPTY,
                              Name('default'),
                              Description('')
                              )


    variant.add_gate(gate)

    component.add_variant(variant)




    uuid_symbol_variant = uuid('sym', '{}_{}'.format(def_name,variant_name), 'sym')
    uuid_variant_variant = _uuid('variant-{}'.format(variant_name))
    
    if uuid_symbol_default != uuid_symbol_variant :

        iunits = int(units)
        variant = Variant(  uuid_variant_variant,
                              Norm.EMPTY,
                              Name('{}'.format(variant_name)),
                              Description('')
                              )

        position =0.0
        for u in range(1, iunits+1):
    
          uuid_symbol_variant = uuid('sym', '{}_{}_{}'.format(def_name,u,variant_name), 'sym')
          uuid_gate_variant = _uuid('gate-{}_{}'.format(u,variant_name))

          gate = Gate(
            uuid_gate_variant,
            SymbolUUID(uuid_symbol_variant),
            Position(0.0, position),
            Rotation(0.0),
            Required(True),
            Suffix(''),
          )
   
          position = position + 100.0
          
          for p in range(1, num_of_pins+ 1):

              if u == int(pad_unit[p-1]) :

                    gate.add_pin_signal_map(
                       PinSignalMap(uuid_pins[p - 1],
                       SignalUUID(uuid_signals[p - 1]),
                       TextDesignator.SYMBOL_PIN_NAME,
                       ))

          variant.add_gate(gate)

        component.add_variant(variant)







      




      
    



    component.serialize(dirpath)
      
    cmp_dir_path = path.join(dirpath, uuid_cmp)
    if not (path.exists(cmp_dir_path) and path.isdir(cmp_dir_path)):
            makedirs(cmp_dir_path)
    with open(path.join(cmp_dir_path, '.librepcb-cmp'), 'w') as f:
            f.write('0.1\n')
    with open(path.join(cmp_dir_path, 'component.lp'), 'w') as f:
            f.write(str(component))
            f.write('\n')

    print('                          :Wrote component {} {}'.format(def_name, uuid_cmp))

            
if __name__ == '__main__':
    def _make(dirpath: str) -> None:
        if not (path.exists(dirpath) and path.isdir(dirpath)):
            makedirs(dirpath)
    _make('out')
    _make('out/{}'.format(group_name))
    _make('out/{}/cmp'.format(group_name))


    
    generate_cmp(
        cvs_file=cvs_file,
        dirpath='out/{}/cmp'.format(group_name),
        author=author,
        version=version,
        keywords=keywords,
        cmpcat=cmpcat,
        default_value='{{PARTNUMBER or DEVICE or COMPONENT}}',
        create_date=create_date,
    )

    save_cache(uuid_cache_file, uuid_cache)
