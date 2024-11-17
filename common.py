"""
Common functionality for generator scripts.
"""
import collections
import csv
import re
from datetime import datetime
from os import makedirs, path

from typing import Any, Dict, Iterable, List, OrderedDict, Union

# String escape sequences
STRING_ESCAPE_SEQUENCES = (
    ('\\', '\\\\'),  # Must be the first one to avoid recursion!
    ('\b', '\\b'),
    ('\f', '\\f'),
    ('\n', '\\n'),
    ('\r', '\\r'),
    ('\t', '\\t'),
    ('\v', '\\v'),
    ('"',  '\\"'),
)


def init_cache(uuid_cache_file: str) -> Dict[str, str]:
    print('Loading cache: {}'.format(uuid_cache_file))
    uuid_cache: OrderedDict[str, str] = collections.OrderedDict()
    try:
        with open(uuid_cache_file, 'r') as f:
            reader = csv.reader(f, delimiter=',', quotechar='"')
            for row in reader:
                uuid_cache[row[0]] = row[1]
    except FileNotFoundError:
        pass
    return uuid_cache


def save_cache(uuid_cache_file: str, uuid_cache: Dict[str, str]) -> None:
    print('Saving cache: {}'.format(uuid_cache_file))
    with open(uuid_cache_file, 'w') as f:
        writer = csv.writer(f, delimiter=',', quotechar='"', lineterminator='\n')
        for k, v in sorted(uuid_cache.items()):
            writer.writerow([k, v])
    print('Done, cached {} UUIDs'.format(len(uuid_cache)))


def now() -> str:
    """
    Return current timestamp as string.
    """
    return datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'


def escape_string(string: str) -> str:
    """
    Escape a string according to LibrePCB S-Expression escaping rules.
    """
    for search, replacement in STRING_ESCAPE_SEQUENCES:
        string = string.replace(search, replacement)
    return string


def format_float(number: float) -> str:
    """
    Format a float according to LibrePCB normalization rules.
    """
    formatted = '{:.3f}'.format(number)
    if formatted == '-0.000':
        return '0.0'  # Remove useless sign
    if formatted[-1] == '0':
        if formatted[-2] == '0':
            return formatted[:-2]
        return formatted[:-1]
    return formatted


def format_ipc_dimension(number: float, decimal_places: int = 2) -> str:
    """
    Format a dimension (e.g. lead span or height) according to IPC rules.

    Note: Unfortunately the IPC naming conventions do not specify whether
          decimals shall be rounded or truncated. But it seems usually they
          are truncated, even in the "Footprint Expert" software from
          https://www.pcblibraries.com/. So let's do it the same way to
          get consistent names.
    """
    number *= pow(10, decimal_places)
    # Note: Round to 1nm before truncating to avoid wrong results due to
    # inaccurate calculations leading in numbers like 0.79999999999999.
    return str(int(round(number, 6 - decimal_places)))


def indent(level: int, lines: Iterable[str]) -> List[str]:
    """
    Indent the lines by the specified level.
    """
    return [' ' * level + line for line in lines]


def sign(val: Union[int, float]) -> int:
    """
    Return 1 for positive or zero values, -1 otherwise.
    """
    if val >= 0.0:
        return 1
    else:
        return -1


def get_pad_uuids(base_lib_path: str, pkg_uuid: str) -> Dict[str, str]:
    """
    Return a mapping from pad name to pad UUID.
    """
    with open(path.join(base_lib_path, 'pkg', pkg_uuid, 'package.lp'), 'r') as f:
        lines = f.readlines()
    opt_matches = [
        re.match(r' \(pad ([^\s]*) \(name "([^"]*)"\)\)$', line)
        for line in lines
    ]
    matches = list(filter(None, opt_matches))
    mapping = {}
    for match in matches:
        uuid = match.group(1)
        name = match.group(2)
        mapping[name] = uuid
    assert len(matches) == len(mapping)
    return mapping


def human_sort_key(key: str) -> List[Any]:
    """
    Function that can be used for natural sorting, where "PB2" comes before
    "PB10" and after "PA3".
    """
    def _convert(text: str) -> Union[int, str]:
        return int(text) if text.isdigit() else text

    return [_convert(x) for x in re.split(r'(\d+)', key) if x]


def serialize_common(serializable: Any, output_directory: str, uuid: str, long_type: str, short_type: str) -> None:
    """
    Centralized serialize() implementation shared between Component, Symbol, Device, Package
    """
    dir_path = path.join(output_directory, uuid)
    if not (path.exists(dir_path) and path.isdir(dir_path)):
        makedirs(dir_path)
    with open(path.join(dir_path, f'.librepcb-{short_type}'), 'w', newline='\n') as f:
        f.write('1\n')
    with open(path.join(dir_path, f'{long_type}.lp'), 'w', newline='\n') as f:
        f.write(str(serializable))
        f.write('\n')
