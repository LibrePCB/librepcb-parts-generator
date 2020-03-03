import hashlib

from typing import Dict

import pytest

from generate_stm_mcu import MCU, Pin


def _make_empty_info() -> Dict[str, str]:
    return {
        'names': {
            'name': 'STM32F3xxxx',
            'ref': '',
            'family': 'STM32F3',
        },
        'package': '',
        'info': {
            'flash': '',
            'ram': '',
            'io': '',
            'frequency': '',
        },
    }


@pytest.mark.parametrize(['mcu_ref', 'expected'], [
    ('STM32F429NEHx', 'STM32F429NxHx'),
    ('STM32L552CETxP', 'STM32L552CxTxP'),
])
def test_mcu_ref_without_flash(mcu_ref, expected):
    mcu = MCU(ref=mcu_ref, info=_make_empty_info(), pins=[])
    assert mcu.ref_without_flash == expected


def test_mcu_pinout_hash():
    mcu = MCU(ref='STM32F123XYZx', info=_make_empty_info(), pins=[
        Pin('3', 'PA1', 'IO'),
        Pin('2', 'PA2', 'IO'),
        Pin('1', 'PA15', 'IO'),
        Pin('4', 'PA0', 'ZZ'),
    ])
    assert mcu.pinout_hash == hashlib.sha1(b'io_pa1,io_pa15,io_pa2,zz_pa0').hexdigest()
    assert mcu.component_identifier == ('stm32f123xxzx~' + mcu.pinout_hash)


def test_mcu_ref_for_flash_variants_multiple():
    mcu = MCU(ref='STM32F429IGHx', info=_make_empty_info(), pins=[])
    assert mcu.ref_for_flash_variants(['STM32F429IEHx', 'STM32F429IGHx', 'STM32F429IIHx']) == 'STM32F429I[EGI]Hx'


def test_mcu_ref_for_flash_variants_single():
    mcu = MCU(ref='STM32F429IGHx', info=_make_empty_info(), pins=[])
    assert mcu.ref_for_flash_variants(['STM32F429IGHx']) == 'STM32F429IGHx'


@pytest.mark.parametrize(['pin_name', 'expected'], [
    ('PC14OSC32_IN', 'PC14-OSC32_IN'),
    ('PC3 / OSC', 'PC3-OSC'),
    ('PC3/ OSC', 'PC3-OSC'),
])
def test_cleanup_pin_name(pin_name, expected):
    mcu = MCU(ref='STM32L071KBTx', info=_make_empty_info(), pins=[])
    assert mcu._cleanup_pin_name(pin_name) == expected
