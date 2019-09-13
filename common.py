"""
Common functionality for generator scripts.
"""
import collections
import csv
import re
from datetime import datetime

from typing import Dict, Iterable, List, Union

# Commonly used dimensions
COURTYARD_LINE_WIDTH = 0.1


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


def format_float(number: float) -> str:
    """
    Format a float according to LibrePCB normalization rules.
    """
    if number == -0.0:  # Returns true for 0.0 too, but that doesn't matter
        number = 0.0
    formatted = '{:.3f}'.format(number)
    if formatted[-1] == '0':
        if formatted[-2] == '0':
            return formatted[:-2]
        return formatted[:-1]
    return formatted


def format_ipc_dimension(number: float, decimal_places: int = 2) -> str:
    """
    Format a dimension (e.g. lead span or height) according to IPC rules.
    """
    formatted = '{:.2f}'.format(number)
    stripped = re.sub(r'^0\.', '', formatted)
    return stripped.replace('.', '')


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
        ' (width {}) (fill false) (grab_area false)'.format(COURTYARD_LINE_WIDTH),
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
