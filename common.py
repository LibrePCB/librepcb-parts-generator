"""
Common functionality for generator scripts.
"""
import collections
import csv
from datetime import datetime


def init_cache(uuid_cache_file: str) -> collections.OrderedDict:
    print('Loading cache: {}'.format(uuid_cache_file))
    uuid_cache = collections.OrderedDict()
    try:
        with open(uuid_cache_file, 'r') as f:
            reader = csv.reader(f, delimiter=',', quotechar='"')
            for row in reader:
                uuid_cache[row[0]] = row[1]
    except FileNotFoundError:
        pass
    return uuid_cache


def save_cache(uuid_cache_file: str, uuid_cache: collections.OrderedDict) -> None:
    print('Saving cache: {}'.format(uuid_cache_file))
    with open(uuid_cache_file, 'w') as f:
        writer = csv.writer(f, delimiter=',', quotechar='"', lineterminator='\n')
        for k, v in uuid_cache.items():
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
    return '{:.2f}'.format(number).replace('0.', '').replace('.', '')
