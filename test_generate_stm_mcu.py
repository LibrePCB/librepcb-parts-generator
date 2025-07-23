from typing import Any, Dict

import pytest

from generate_stm_mcu import MCU


def _make_empty_info(flash_size: int = 0) -> Dict[str, Any]:
    return {
        'names': {
            'name': 'STM32F3xxxx',
            'ref': '',
            'family': 'STM32F3',
        },
        'package': '',
        'gpio_version': '',
        'info': {
            'flash': flash_size,
            'ram': '',
            'io': '',
            'frequency': '',
        },
    }


@pytest.mark.parametrize(
    ['mcu_ref', 'expected', 'flash_size'],
    [
        ('STM32F429NEHx', 'STM32F429NxHx', 512),
        ('STM32L552CETxP', 'STM32L552CxTxP', 512),
        ('STM32MP153CADx', 'STM32MP153CADx', 0),
    ],
)
def test_mcu_ref_without_flash(mcu_ref, expected, flash_size):
    mcu = MCU(ref=mcu_ref, info=_make_empty_info(flash_size), pins=[])
    assert mcu.ref_without_flash == expected


def test_mcu_ref_for_flash_variants_multiple():
    mcu = MCU(ref='STM32F429IGHx', info=_make_empty_info(), pins=[])
    assert (
        mcu.ref_for_flash_variants(['STM32F429IEHx', 'STM32F429IGHx', 'STM32F429IIHx'])
        == 'STM32F429I[EGI]Hx'
    )


def test_mcu_ref_for_flash_variants_single():
    mcu = MCU(ref='STM32F429IGHx', info=_make_empty_info(), pins=[])
    assert mcu.ref_for_flash_variants(['STM32F429IGHx']) == 'STM32F429IGHx'


@pytest.mark.parametrize(
    ['pin_name', 'expected'],
    [
        # Oscillator normalization
        ('PC14OSC32_IN', 'PC14-OSC32_IN'),
        ('PC3 / OSC', 'PC3-OSC'),
        ('PC3/ OSC', 'PC3-OSC'),
        # Everything after a space is stripped out
        ('PH3-BOOT0 (BOOT0)', 'PH3-BOOT0'),
        ('PC15-OSC32_OUT (OSC32_OUT)', 'PC15-OSC32_OUT'),
        ('PA13 (JTMS/SWDIO)', 'PA13'),
    ],
)
def test_cleanup_pin_name(pin_name, expected):
    mcu = MCU(ref='STM32L071KBTx', info=_make_empty_info(), pins=[])
    assert mcu._cleanup_pin_name(pin_name) == expected


def test_signal_name_validation():
    mcu = MCU(ref='STM32L071KBTx', info=_make_empty_info(), pins=[])
    with pytest.raises(AssertionError):
        mcu._cleanup_pin_name('Hel(lo world')
