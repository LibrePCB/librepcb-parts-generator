"""
Common functionality for generator scripts.
"""
import collections
import csv


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
