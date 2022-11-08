
# importing csv module
import csv

import argparse
from os import makedirs, path
from uuid import uuid4
from typing import Optional
from common import init_cache, now, save_cache
from entities.common import (
    Align, Angle, Author, Category, Circle, Created, Description, Diameter, Fill, GrabArea, Height, Keywords, Layer, Length,
    Name, Polygon, Position, Rotation, Text, Value, Version, Vertex, Width
)
from entities.symbol import Pin as SymbolPin
from entities.symbol import Symbol

parser = argparse.ArgumentParser(description='create a symbol from csv file')
parser.add_argument("--design")
parser.add_argument("--group")
parser.add_argument("--directory")

args = parser.parse_args()
design_name = args.design
group_name = args.group
directory_name = args.directory

# initializing
boilerplate_raw_data = []
cvs_raw_data = []


"""

"""

generator = 'librepcb-parts-generator (generate_logic_sym.py)'


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


unit = 2.54
width = 2.54
line_width = 0.25
pkg_text_height = 1.0
sym_text_height = 2.54
descr = ""
boilerplate_cvs_file = 'Boilerplate_{}.csv'.format(group_name)

with open(boilerplate_cvs_file, 'r') as CSVBfile:
    # creating a csv reader object
    CSVbreader = csv.reader(CSVBfile)
    # extracting each data row one by one
    for brow in CSVbreader:
        boilerplate_raw_data.append(brow)

    print("                                            Total no. of rows: %d" % (CSVbreader.line_num))
    num_of_brows = CSVbreader.line_num

for brow in boilerplate_raw_data[:num_of_brows]:
    # parsing each column of a row
    row_type = brow[0]
    if row_type == "CREATE":
        create_date = brow[1]
    if row_type == "VERSION":
        version = brow[1]
    if row_type == "AUTHOR":
        author = brow[1]
    if row_type == "KEYWORDS":
        keywords = brow[1]
        if len(brow) > 2:
            for p in range(2, len(brow)):
                keywords = '{},{}'.format(keywords, brow[p])

print("            Create Date  : {}".format(create_date))
print("            Version  : {}".format(version))
print("            Author   : {}".format(author))
print("            Keywords  : {}".format(keywords))


cvs_file = '{}{}.csv'.format(directory_name, design_name)

with open(cvs_file, 'r') as CSVxfile:
    # creating a csv reader object
    CSVxreader = csv.reader(CSVxfile)
    # extracting each data row one by one
    for row in CSVxreader:
        cvs_raw_data.append(row)

    print("                                            Total no. of rows: %d" % (CSVxreader.line_num))
    num_of_rows = CSVxreader.line_num

for row in cvs_raw_data[:num_of_rows]:
    # parsing each column of a row
    row_type = row[0]
    if row_type == "KEYWORDS":
        keywords = '{},{}'.format(keywords, row[1])
    if row_type == "DEF":
        def_name = row[1]
    if row_type == "DESCR":
        descr = row[1]

uuid_cmpcat_file = 'uuid_cache_{}_cmpcat.csv'.format(group_name)
uuid_cache = init_cache(uuid_cmpcat_file)
cmpcat = uuid('cmpcat', def_name, "cmpcat")
save_cache(uuid_cmpcat_file, uuid_cache)

# Initialize UUID cache
uuid_cache_file = 'uuid_cache_{}.csv'.format(group_name)
uuid_cache = init_cache(uuid_cache_file)


def generate_sym(
    cvs_file: str,
    dirpath: str,
    author: str,
    keywords: str,
    descr: str,
    version: str,
    cmpcat: str,
    create_date: Optional[str],
) -> None:
    category = 'sym'
    pad_type = []
    pad_name = []
    pad_posx = []
    pad_posy = []
    pad_length = []
    pad_orientation = []
    uuid_pins = []
    num_of_pins = 0
    low_x = 0
    low_y = 0
    high_x = 0
    high_y = 0
    scale = 1.000

    for row in cvs_raw_data[:num_of_rows]:
        # parsing each column of a row
        row_type = row[0]

        if row_type == "SCALE":
            scale = float(row[1])

        if row_type == "DEF":
            def_name = row[1]
        if row_type == "PIN":

            pin_type = row[2]
            if pin_type == "R":
                pad_orientation.append(0.0)
            if pin_type == "L":
                pad_orientation.append(180.0)
            if pin_type == "D":
                pad_orientation.append(270.0)

            if pin_type == "U":
                pad_orientation.append(90.0)

            pad_name.append(row[1])
            pad_type.append(row[2])
            pad_posx.append(float(row[3]) * unit)
            pad_posy.append(float(row[4]) * unit)
            pad_length.append(float(row[5]) * unit)
            uuid_pins.append(uuid('sym', def_name, 'pin-{}'.format(row[1])))
            num_of_pins = num_of_pins + 1

    uuid_sym = uuid('sym', '{}'.format(def_name), 'sym')

    def _uuid(identifier: str) -> str:
        return uuid(category, def_name, identifier)
    polygon_cnt = 1
    uuid_text_name = _uuid('text-name')
    uuid_text_value = _uuid('text-value')
    sym_name = '{}'.format(def_name)

    # General info
    symbol = Symbol(
        uuid_sym,
        Name('{}'.format(sym_name)),
        Description('{}\\ncreated from file---  {}.\\n'
                    'Generated with {}'.format(descr, cvs_file, generator)),
        Keywords('{}'.format( keywords)),
        Author(author),
        Version(version),
        Created(create_date or now()),
        Category(cmpcat),
    )

    for p in range(1, num_of_pins + 1, 1):
        # parsing each column of a row
        pin_type = pad_type[p - 1]
        pin_name = pad_name[p - 1]
        pin_posx = pad_posx[p - 1]
        pin_posy = pad_posy[p - 1]
        pin_orient = pad_orientation[p - 1]
        pin_length = pad_length[p - 1]
        pin = SymbolPin(
            uuid_pins[p - 1],
            Name( pin_name),
            Position(pin_posx, pin_posy),
            Rotation(pin_orient),
            Length(pin_length)
        )

        symbol.add_pin(pin)

    # Polygons
    for row in cvs_raw_data[:num_of_rows]:
        # parsing each column of a row
        row_type = row[0]
        if row_type == "POLY":
            line_width = float(row[1]) * unit
            fill = row[2]
            if fill == "F":
                fill_str = "True"
                uuid_polygon = _uuid('polygon-contour')
                polygon = Polygon(
                    uuid_polygon,
                    Layer('sym_outlines'),
                    Width(line_width),
                    Fill(False),
                    GrabArea(fill_str)
                )
            else:
                fill_str = "False"
                uuid_polygon = uuid('sym', '{}-polygon-{}'.format(def_name, polygon_cnt), 'sym')
                polygon_cnt = polygon_cnt + 1
                polygon = Polygon(
                    uuid_polygon,
                    Layer('sym_outlines'),
                    Width(line_width),
                    Fill(False),
                    GrabArea(fill_str)
                )

        if row_type == "POLYPT":
            print('POLYPT  {} {} {}'.format( row[1], row[2], row[3]))
            poly_x = float(row[1]) * unit / scale
            poly_y = float(row[2]) * unit / scale
            poly_angle = float(row[3])
            polygon.add_vertex(Vertex(Position(poly_x, poly_y), Angle(poly_angle)))

        if row_type == "POLYST":
            print('POLY Stop ')
            symbol.add_polygon(polygon)

        if row_type == "RECT":
            low_x = float(row[1]) * unit / scale
            low_y = float(row[2]) * unit / scale
            high_x = float(row[3]) * unit / scale
            high_y = float(row[4]) * unit / scale
            print('Rectangle ')
            uuid_polygon = uuid('sym', '{}-polygon-{}'.format(def_name, polygon_cnt), 'sym')
            polygon_cnt = polygon_cnt + 1
            polygon = Polygon(
                uuid_polygon,
                Layer('sym_outlines'),
                Width(line_width),
                Fill(False),
                GrabArea(True)
            )
            polygon.add_vertex(Vertex(Position(low_x, low_y), Angle(0.0)))
            polygon.add_vertex(Vertex(Position(low_x, high_y), Angle(0.0)))
            polygon.add_vertex(Vertex(Position(high_x, high_y), Angle(0.0)))
            polygon.add_vertex(Vertex(Position(high_x, low_y), Angle(0.0)))
            polygon.add_vertex(Vertex(Position(low_x, low_y), Angle(0.0)))
            symbol.add_polygon(polygon)

        if row_type == "CIRC":
            line_width = float(row[1]) * unit / scale
            pos_x = float(row[2]) * unit / scale
            pos_y = float(row[3]) * unit / scale
            dia = float(row[4]) * unit / scale
            uuid_polygon = uuid('sym', '{}-polygon-{}'.format(def_name, polygon_cnt), 'sym')
            polygon_cnt = polygon_cnt + 1
            print('Circle ')
            circle = Circle(
                uuid_polygon,
                Layer('sym_outlines'),
                Width(line_width),
                Fill(False),
                GrabArea(False),
                Diameter(dia),
                Position(pos_x, pos_y)
            )
            symbol.add_circle(circle)

        if row_type == "TEXT":
            pos_x = float(row[1]) * unit / scale
            pos_y = float(row[2]) * unit / scale
            textfield = row[3]
            if textfield == "NAME":
                text = Text(uuid_text_name, Layer('sym_names'), Value('{{NAME}}'), Align('right bottom'), Height(sym_text_height), Position(pos_x, pos_y), Rotation(0.0))
            if textfield == "VALUE":
                text = Text(uuid_text_value, Layer('sym_values'), Value('{{VALUE}}'), Align('right top'), Height(sym_text_height), Position(pos_x, pos_y), Rotation(0.0))
            symbol.add_text(text)

    sym_dir_path = path.join(dirpath, uuid_sym)
    if not (path.exists(sym_dir_path) and path.isdir(sym_dir_path)):
        makedirs(sym_dir_path)
    with open(path.join(sym_dir_path, '.librepcb-sym'), 'w') as f:
        f.write('0.1\n')
    with open(path.join(sym_dir_path, 'symbol.lp'), 'w') as f:
        f.write(str(symbol))
        f.write('\n')

    print('                                            {}: Wrote symbol {}'.format( def_name, uuid_sym))


if __name__ == '__main__':
    def _make(dirpath: str) -> None:
        if not (path.exists(dirpath) and path.isdir(dirpath)):
            makedirs(dirpath)
    _make('out')
    _make('out/{}'.format(group_name))
    _make('out/{}/sym'.format(group_name))

    generate_sym(
        cvs_file=cvs_file,
        dirpath='out/{}/sym'.format(group_name),
        author=author,
        version=version,
        keywords=keywords,
        descr=descr,
        cmpcat=cmpcat,
        create_date=create_date,
    )

    save_cache(uuid_cache_file, uuid_cache)
