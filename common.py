"""
Common functionality for generator scripts.
"""
import collections
import csv
import os.path
import re
from datetime import datetime

from typing import Any, Dict, Iterable, List, Union

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
    uuid_cache = collections.OrderedDict()  # type: Dict[str, str]
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


def generate_courtyard(
    uuid: str,
    max_x: float,
    max_y: float,
    excess_x: float,
    excess_y: float,
) -> List[str]:
    """
    Generate a rectangular courtyard polygon.

    Args:
        uuid:
            The polygon UUID
        max_x:
            The half width (x) of the maximum boundary
        max_y:
            The half height (y) of the maximum boundary
        excess_x:
            Courtyard excess in x direction
        excess_y:
            Courtyard excess in y direction

    """
    dx = format_float(max_x + excess_x)
    dy = format_float(max_y + excess_y)
    return [
        '(polygon {} (layer {})'.format(uuid, 'top_courtyard'),
        ' (width {}) (fill false) (grab_area false)'.format(0.0),
        ' (vertex (position -{} {}) (angle 0.0))'.format(dx, dy),  # NW
        ' (vertex (position {} {}) (angle 0.0))'.format(dx, dy),  # NE
        ' (vertex (position {} -{}) (angle 0.0))'.format(dx, dy),  # SE
        ' (vertex (position -{} -{}) (angle 0.0))'.format(dx, dy),  # SW
        ' (vertex (position -{} {}) (angle 0.0))'.format(dx, dy),  # NW
        ')',
    ]


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
    with open(os.path.join(base_lib_path, 'pkg', pkg_uuid, 'package.lp'), 'r') as f:
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
