"""
Generate dual mosfet devices.
"""
from os import makedirs, path
from uuid import uuid4

from typing import Any, Dict, Iterable, List, Optional

from common import init_cache, now, save_cache

generator = 'librepcb-parts-generator (generate_mosfet_dual.py)'

# Initialize UUID cache
uuid_cache_file = 'uuid_cache_mosfet_dual.csv'
uuid_cache = init_cache(uuid_cache_file)


def uuid(category: str, full_name: str, identifier: str) -> str:
    """
    Return a uuid for the specified pin.

    Params:
        category:
            For example 'cmp' or 'pkg'.
        full_name:
            For example "RESC3216X65".
        identifier:
            For example 'pad-1' or 'pin-13'.
    """
    key = '{}-{}-{}'.format(category, full_name, identifier).lower().replace(' ', '~')
    if key not in uuid_cache:
        uuid_cache[key] = str(uuid4())
    return uuid_cache[key]


class PackageConfig:
    def __init__(
        self,
        uuid_pkg: str,
        uuid_pads: List[str],
    ):
        self.uuid_pkg = uuid_pkg
        self.uuid_pads = uuid_pads


PACKAGES = {
    'SOIC127P600X175-8': PackageConfig(
        'ffbf2bed-9155-45a9-b154-2f766c7f9019',
        [
            '1a3b50b0-379c-40d9-a015-c1117ee4d0ff',  # 1
            '030ad5ef-b6fc-4884-866c-74dc806f28a9',  # 2
            '77f3d8f5-8e7f-4fab-906a-76fe905b886a',  # 3
            'e7d9d938-5347-44d2-9bb5-63543f981b49',  # 4
            '1774652b-09d3-4961-8af6-2e0d0272cde3',  # 5
            '5f747ca7-c5d6-41a1-b16b-d08f7df7050a',  # 6
            '1a3d74c1-cd55-49fa-9717-df952d5ac40b',  # 7
            'ca7a042a-80b0-4499-bb1e-f4a4c285bfa5',  # 8
        ],
    ),
    'SOT95P280X145-6': PackageConfig(
        'f8289e96-50c9-4db1-8def-e85f5e652c2c',
        [
            '7e576b6c-3899-477b-8d29-1e45ff5b7d54',  # 1
            '43a2ca57-3cb7-475d-bbfc-96634b5416e7',  # 2
            '7f6eaa1a-9d2e-4959-a1d5-c0973115db42',  # 3
            'c058c65b-3482-4a6f-9efa-d5aeb1fd2ab1',  # 4
            '0bc8940c-ff27-4a71-8bc0-816c93d4f950',  # 5
            '6e7a460e-bb32-4801-91fd-6e6d5155ac37',  # 6
        ],
    ),
}


# Dual MOSFET component signal UUIDs
SIGNALS = {
    'sn': '98197955-ca0a-40c7-9fd8-2d40fa733c85',
    'dn': 'fa09c163-2b6c-4235-8e2a-20b7f3b5387b',
    'gn': 'd8cf18ee-823a-4e73-b2ce-e4e0fc1b7486',
    'sp': 'e810e75b-a490-4e5f-8d0c-aa2a4553e39d',
    'dp': 'f07f1ca0-50ed-400a-95e3-2dcb7812bd0e',
    'gp': '3202a2ee-d8be-4d8a-a0f4-2cbbd7022071',
}


class FetConfig:
    def __init__(
        self,
        name: str,  # String, e.g. "DMC4040SSD"
        max_voltage: int,
        package: str,
        signals: List[str],
        datasheets: Optional[Iterable[str]],
    ):
        self.name = name
        self.max_voltage = max_voltage
        self.package = package
        self.signals = signals
        self.datasheets = datasheets


def generate_dev(
    dirpath: str,
    name: str,
    author: str,
    description: str,
    version: str,
    keywords: str,
    create_date: Optional[str],
    uuid_cat: str,
    uuid_cmp: str,
    configs: Iterable[FetConfig],
) -> None:
    for fet_config in configs:
        lines = []

        fmt_params = {
            'name': fet_config.name,
            'max_voltage': fet_config.max_voltage,
        }  # type: Dict[str, Any]
        full_name = name.format(**fmt_params)
        full_desc = description.format(**fmt_params)

        # Package
        package_config = PACKAGES[fet_config.package]

        # UUIDs
        uuid_dev = uuid('dev', full_name, 'dev')
        uuid_pkg = package_config.uuid_pkg
        uuid_pads = package_config.uuid_pads
        uuid_signals = [SIGNALS[s] for s in fet_config.signals]
        if not len(uuid_pads) == len(uuid_signals):
            raise ValueError('Pads and signals have different length')

        # Datasheet section in description
        if fet_config.datasheets:
            if isinstance(fet_config.datasheets, list):
                datasheet_parts = ['Datasheets:']
                datasheet_parts.extend('- {}'.format(d) for d in fet_config.datasheets)
                datasheet = r'\n'.join(datasheet_parts) + r'\n\n'
            else:
                datasheet = 'Datasheet: {}\\n\\n'.format(fet_config.datasheets)
        else:
            datasheet = ''

        print('Generating dev "{}": {}'.format(full_name, uuid_dev))
        lines.append('(librepcb_device {}'.format(uuid_dev))
        lines.append(' (name "{}")'.format(full_name))
        lines.append(' (description "{}\\n\\n{}Generated with {}")'.format(full_desc, datasheet, generator))
        lines.append(' (keywords "{}")'.format(keywords))
        lines.append(' (author "{}")'.format(author))
        lines.append(' (version "{}")'.format(version))
        lines.append(' (created {})'.format(create_date or now()))
        lines.append(' (deprecated false)')
        lines.append(' (category {})'.format(uuid_cat))
        lines.append(' (component {})'.format(uuid_cmp))
        lines.append(' (package {})'.format(uuid_pkg))
        pad_signal_mappings = []
        for (pad, signal) in zip(uuid_pads, uuid_signals):
            pad_signal_mappings.append(' (pad {} (signal {}))'.format(pad, signal))
        lines.extend(sorted(pad_signal_mappings))
        lines.append(')')

        dev_dir_path = path.join(dirpath, uuid_dev)
        if not (path.exists(dev_dir_path) and path.isdir(dev_dir_path)):
            makedirs(dev_dir_path)
        with open(path.join(dev_dir_path, '.librepcb-dev'), 'w') as f:
            f.write('0.1\n')
        with open(path.join(dev_dir_path, 'device.lp'), 'w') as f:
            f.write('\n'.join(lines))
            f.write('\n')


if __name__ == '__main__':
    def _make(dirpath: str) -> None:
        if not (path.exists(dirpath) and path.isdir(dirpath)):
            makedirs(dirpath)
    _make('out')
    _make('out/mosfet_dual')
    _make('out/mosfet_dual/diodes_inc')
    _make('out/mosfet_dual/diodes_inc/dev')
    # Diodes Incorporated
    generate_dev(
        dirpath='out/mosfet_dual/diodes_inc/dev',
        name='{name}',
        author='Danilo B.',
        description='Diodes Incorporated {name} Dual MOSFET N/P-Channel {max_voltage}V.',
        version='0.1',
        keywords='mosfet,p-channel,p-fet,n-channel,n-fet,dual',
        create_date='2019-02-04T20:23:03Z',
        uuid_cat='e9663545-80dd-4658-9357-d4ef62e55168',
        uuid_cmp='9d043413-9574-4727-af3a-21c5623cffae',
        configs=[
            # SOIC127P600X175-8
            FetConfig('DMC2020USD', 20, 'SOIC127P600X175-8', [
                'sn', 'gn', 'sp', 'gp', 'dp', 'dp', 'dn', 'dn',
            ], 'https://www.diodes.com/assets/Datasheets/DMC2020USD.pdf'),
            FetConfig('DMC3016LSD', 30, 'SOIC127P600X175-8', [
                'sn', 'gn', 'sp', 'gp', 'dp', 'dp', 'dn', 'dn',
            ], 'https://www.diodes.com/assets/Datasheets/DMC3016LSD.pdf'),
            FetConfig('DMC3021LSD[Q]', 30, 'SOIC127P600X175-8', [
                'sn', 'gn', 'sp', 'gp', 'dp', 'dp', 'dn', 'dn',
            ], [
                'https://www.diodes.com/assets/Datasheets/ds32152.pdf',
                'https://www.diodes.com/assets/Datasheets/DMC3021LSDQ.pdf',
            ]),
            FetConfig('DMC3025LSD[Q]', 30, 'SOIC127P600X175-8', [
                'sn', 'gn', 'sp', 'gp', 'dp', 'dp', 'dn', 'dn',
            ], [
                'https://www.diodes.com/assets/Datasheets/DMC3025LSD.pdf',
                'https://www.diodes.com/assets/Datasheets/DMC3025LSDQ.pdf',
            ]),
            FetConfig('DMC3028LSD[Q[X]]', 30, 'SOIC127P600X175-8', [
                'sn', 'gn', 'sp', 'gp', 'dp', 'dp', 'dn', 'dn',
            ], [
                'https://www.diodes.com/assets/Datasheets/DMC3028LSD.pdf',
                'https://www.diodes.com/assets/Datasheets/DMC3028LSDX.pdf',
                'https://www.diodes.com/assets/Datasheets/DMC3028LSDXQ.pdf',
            ]),
            FetConfig('DMC3032LSD', 30, 'SOIC127P600X175-8', [
                'sn', 'gn', 'sp', 'gp', 'dp', 'dp', 'dn', 'dn',
            ], 'https://www.diodes.com/assets/Datasheets/ds32153.pdf'),
            FetConfig('DMC4015SSD', 40, 'SOIC127P600X175-8', [
                'sn', 'gn', 'sp', 'gp', 'dp', 'dp', 'dn', 'dn',
            ], 'https://www.diodes.com/assets/Datasheets/DMC4015SSD.pdf'),
            FetConfig('DMC4028SSD', 40, 'SOIC127P600X175-8', [
                'sn', 'gn', 'sp', 'gp', 'dp', 'dp', 'dn', 'dn',
            ], 'https://www.diodes.com/assets/Datasheets/DMC4028SSD.pdf'),
            FetConfig('DMC4029SSD', 40, 'SOIC127P600X175-8', [
                'sn', 'gn', 'sp', 'gp', 'dp', 'dp', 'dn', 'dn',
            ], 'https://www.diodes.com/assets/Datasheets/DMC4029SSD.pdf'),
            FetConfig('DMC4040SSD[Q]', 40, 'SOIC127P600X175-8', [
                'sn', 'gn', 'sp', 'gp', 'dp', 'dp', 'dn', 'dn',
            ], [
                'https://www.diodes.com/assets/Datasheets/ds32120.pdf',
                'https://www.diodes.com/assets/Datasheets/DMC4040SSDQ.pdf',
            ]),
            FetConfig('DMC4047LSD', 40, 'SOIC127P600X175-8', [
                'sn', 'gn', 'sp', 'gp', 'dp', 'dp', 'dn', 'dn',
            ], 'https://www.diodes.com/assets/Datasheets/DMC4047LSD.pdf'),
            FetConfig('DMC4050SSD[Q]', 40, 'SOIC127P600X175-8', [
                'sn', 'gn', 'sp', 'gp', 'dp', 'dp', 'dn', 'dn',
            ], 'https://www.diodes.com/assets/Datasheets/DS33310.pdf'),
            FetConfig('DMC6040SSD[Q]', 60, 'SOIC127P600X175-8', [
                'sn', 'gn', 'sp', 'gp', 'dp', 'dp', 'dn', 'dn',
            ], [
                'https://www.diodes.com/assets/Datasheets/DMC6040SSD.pdf',
                'https://www.diodes.com/assets/Datasheets/DMC6040SSDQ.pdf',
            ]),

            # SOT95P280X145-6
            FetConfig('DMC2053UVT', 20, 'SOT95P280X145-6', ['gn', 'sp', 'gp', 'dp', 'sn', 'dn'],
                      'https://www.diodes.com/assets/Datasheets/DMC2053UVT.pdf'),
            FetConfig('DMC2057UVT', 20, 'SOT95P280X145-6', ['gn', 'sp', 'gp', 'dp', 'sn', 'dn'],
                      'https://www.diodes.com/assets/Datasheets/DMC2057UVT2.pdf'),
            FetConfig('DMC3071LVT', 30, 'SOT95P280X145-6', ['gn', 'sp', 'gp', 'dp', 'sn', 'dn'],
                      'https://www.diodes.com/assets/Datasheets/DMC3071LVT.pdf'),
            FetConfig('DMC3730UVT', 25, 'SOT95P280X145-6', ['gn', 'sp', 'gp', 'dp', 'sn', 'dn'],
                      'https://www.diodes.com/assets/Datasheets/DMC3730UVT.pdf'),
            FetConfig('DMG6601LVT', 30, 'SOT95P280X145-6', ['gn', 'sp', 'gp', 'dp', 'sn', 'dn'],
                      'https://www.diodes.com/assets/Datasheets/DMG6601LVT.pdf'),
            FetConfig('DMG6602SVTQ', 30, 'SOT95P280X145-6', ['gn', 'sp', 'gp', 'dp', 'sn', 'dn'],
                      'https://www.diodes.com/assets/Datasheets/DMG6602SVTQ.pdf'),
        ],
    )
    save_cache(uuid_cache_file, uuid_cache)
