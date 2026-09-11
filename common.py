"""
Common functionality for generator scripts.
"""

import collections
import csv
import math
import re
from datetime import datetime
from os import path
from uuid import uuid4

from typing import Any, Dict, Generator, List, Literal, OrderedDict, Union

from entities.common import Angle, Fill, GrabArea, Layer, Polygon, Position, Vertex, Width


class SubCache:
    def __init__(self, base: Union['UuidCache', 'SubCache'], *prefixes: Any):
        self.base = base
        self.prefixes = prefixes

    def get(self, *args: Any) -> str:
        return self.base.get(*self.prefixes, *args)

    def sub_cache(self, *prefixes: Any) -> 'SubCache':
        return SubCache(self, *prefixes)


class UuidCache:
    def __init__(self, filename: str, stale_check: bool = True):
        self.filename = filename
        self.used_keys: set[str] = set()
        self.entered = False
        self.stale_check = stale_check

        self.data: OrderedDict[str, str] = collections.OrderedDict()
        print(f'Loading cache: {filename}')
        try:
            with open(self.filename, 'r') as f:
                reader = csv.reader(f, delimiter=',', quotechar='"')
                for row in reader:
                    self.data[row[0]] = row[1]
        except FileNotFoundError:
            print('Cache file {filename} not found, building new cache')
        print(f'Cache has {len(self.data)} entries')

    def __enter__(self) -> 'UuidCache':
        self.used_keys = set()
        self.entered = True
        return self

    def __exit__(self, exception: Any, value: Any, traceback: Any) -> None:
        if not exception and self.entered:
            self.check_stale()
            self.save_cache()
            self.entered = False

    def save_cache(self) -> None:
        print(f'Saving cache: {self.filename}')
        with open(self.filename, 'w') as f:
            writer = csv.writer(f, delimiter=',', quotechar='"', lineterminator='\n')
            for k, v in sorted(self.data.items()):
                writer.writerow([k, v])
        print(f'Done, cached {len(self.data)} UUIDs')

    def get(self, *args: Any, create: bool = True) -> str:
        key = '-'.join(str(a).lower().replace(' ', '~') for a in args)
        if key not in self.data:
            if self.entered and create:
                self.data[key] = str(uuid4())
            else:
                raise KeyError(
                    f'{key} not found in uuid cache. Entering the context is required for auto-generation'
                )
        self.used_keys.add(key)
        return self.data[key]

    def check_stale(self) -> None:
        if self.stale_check:
            stale_keys = {key for key in self.data if key not in self.used_keys}
            if stale_keys:
                raise RuntimeError(f'There are stale UUIDs in the cache: {stale_keys}')

    def sub_cache(self, *prefixes: Any) -> SubCache:
        return SubCache(self, *prefixes)


def now() -> str:
    """
    Return current timestamp as string.
    """
    return datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'


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
    opt_matches = [re.match(r' \(pad ([^\s]*) \(name "([^"]*)"\)\)$', line) for line in lines]
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


def make_border_rectangle(
    left: float,
    right: float,
    top: float,
    bottom: float,
    width: float,
    direction: Literal['inner', 'outer', 'center'],
) -> list[Vertex]:
    w = (
        width
        / 2
        * {
            'inner': -1.0,
            'center': 0.0,
            'outer': +1.0,
        }[direction]
    )
    line_l = left - w
    line_r = right + w
    line_t = top + w
    line_b = bottom - w

    return [
        Vertex(Position(x, y), Angle(0))
        for x, y in [
            (line_l, line_t),
            (line_l, line_b),
            (line_r, line_b),
            (line_r, line_t),
            (line_l, line_t),
        ]
    ]


def grid_solderpaste(
    uuid_cache: SubCache,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    max_drop_size: float = 1.00,
) -> Generator[Polygon, None, None]:
    # SLUA271c suggests 1x1mm solder drops
    fill_factor = 0.80  # approximated from default pad filling
    num_x = math.ceil((x_max - x_min) / max_drop_size)
    num_y = math.ceil((y_max - y_min) / max_drop_size)
    pitch_x = (x_max - x_min) / num_x
    pitch_y = (y_max - y_min) / num_y
    size_x = pitch_x * fill_factor
    size_y = pitch_y * fill_factor

    for ix in range(num_x):
        for iy in range(num_y):
            center_x = pitch_x * (ix - num_x / 2 + 0.5)
            center_y = pitch_y * (iy - num_y / 2 + 0.5)
            yield Polygon(
                uuid=uuid_cache.get('solderpaste', ix, iy),
                layer=Layer('top_solder_paste'),
                width=Width(0),
                fill=Fill(True),
                grab_area=GrabArea(False),
                vertices=[
                    Vertex(Position(x, y), Angle(0))
                    for x, y in [
                        (center_x - size_x / 2, center_y - size_y / 2),
                        (center_x - size_x / 2, center_y + size_y / 2),
                        (center_x + size_x / 2, center_y + size_y / 2),
                        (center_x + size_x / 2, center_y - size_y / 2),
                        (center_x - size_x / 2, center_y - size_y / 2),
                    ]
                ],
            )
