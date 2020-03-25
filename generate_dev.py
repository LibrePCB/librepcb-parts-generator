
# importing csv module
import csv
import argparse
import collections
from os import makedirs, path
from uuid import uuid4
from typing import Optional, Dict
from common import init_cache, now, save_cache

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
boilerplate_raw_data = []
uuid_pads = []
uuid_signals = []


"""

"""

generator = 'librepcb-parts-generator (generate_dev.py)'


def init_CACHE(uuid_CACHE_file: str) -> Dict[str, str]:
    print('Loading CACHE: {}'.format(uuid_CACHE_file))
    uuid_CACHE = collections.OrderedDict()  # type: Dict[str, str]
    try:
        with open(uuid_CACHE_file, 'r') as f:
            reader = csv.reader(f, delimiter=',', quotechar='"')
            for row in reader:
                uuid_CACHE[row[0]] = row[1]
    except FileNotFoundError:
        pass
    return uuid_CACHE


def save_CACHE(uuid_CACHE_file: str, uuid_CACHE: Dict[str, str]) -> None:
    print('Saving CACHE: {}'.format(uuid_CACHE_file))
    with open(uuid_CACHE_file, 'w') as f:
        writer = csv.writer(f, delimiter=',', quotechar='"', lineterminator='\n')
        for k, v in sorted(uuid_CACHE.items()):
            writer.writerow([k, v])
    print('Done, CACHEd {} UUIDs'.format(len(uuid_CACHE)))


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


def UUID(category: str) -> str:
    """

    """
    key = '{}'.format(category).lower().replace(' ', '~')
    if key not in uuid_CACHE:
        uuid_CACHE[key] = 'none'
    return uuid_CACHE[key]


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
    num_of_rows = CSVxreader.line_num

for row in cvs_raw_data[:num_of_rows]:
    # parsing each column of a row
    row_type = row[0]

    if row_type == "VERSION":
        version = row[1]
    if row_type == "KEYWORDS":
        keywords = row[1]
    if row_type == "DEF":
        def_name = row[1]

# Initialize cmpcat UUID
uuid_cmpcat_file = 'uuid_cache_{}_cmpcat.csv'.format(group_name)
uuid_cache = init_cache(uuid_cmpcat_file)
cmpcat = uuid('cmpcat', def_name, "cmpcat")
save_cache(uuid_cmpcat_file, uuid_cache)


# Initialize UUID cache
uuid_cache_file = 'uuid_cache_{}.csv'.format(group_name)
uuid_cache = init_cache(uuid_cache_file)


uuid_CACHE_file = 'MapFile.csv'
uuid_CACHE = init_CACHE(uuid_CACHE_file)

category = 'dev'
pad_list = []
pad_name = []
lines = []
num_of_pins = 0
package = "none"

for row in cvs_raw_data[:num_of_rows]:
    # parsing each column of a row
    row_type = row[0]

    if row_type == "VERSION":
        version = row[1]
    if row_type == "KEYWORDS":
        keywords = row[1]
    if row_type == "DEF":
        def_name = row[1]
    if row_type == "FOOT":
        package = row[1].lower()
    if row_type == "PIN":
        pad_name.append(row[1])
        pad_list.append(row[3])
        uuid_signals.append(uuid('cmp', def_name, 'signal-{}_{}'. format(row[1], row[3])))
        num_of_pins = num_of_pins + 1

uuid_PKG = UUID(package)
uuid_CACHE_file = 'MapFile.out'
save_CACHE(uuid_CACHE_file, uuid_CACHE)

package = uuid_PKG

print("      device: %s Number of pins %s   Package  %s   UUID  %s" % (def_name, num_of_pins, package, uuid_PKG))
uuid_dev = uuid('dev', def_name, 'dev')
uuid_cmp = uuid('cmp', def_name, 'cmp')

# Initialize UUID cache
uuid_cache_file = 'uuid_cache_pkg.csv'
uuid_cache = init_cache(uuid_cache_file)


uuid_pkg = uuid('pkg', package, 'pkg')


def generate_dev(
    cvs_file: str,
    dirpath: str,
    author: str,
    version: str,
    keywords: str,
    cmpcat: str,
    create_date: Optional[str],
) -> None:

    # General info
    lines.append('(librepcb_device {}'.format(uuid_dev))
    lines.append(' (name "{}")'.format(def_name))
    lines.append(' (description "  ''Generated with {}")'.format(generator))
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
        uuid_pad = uuid('pkg', package, 'pad-{}'.format(pad_list[p - 1]))
        signalmappings.append(' (pad {} (signal {}))'.format(uuid_pad, uuid_signals[p - 1]))
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
        cvs_file=cvs_file,
        dirpath='out/{}/dev'.format(group_name),
        author=author,
        version=version,
        keywords=keywords,
        cmpcat=cmpcat,
        create_date=create_date,
    )
