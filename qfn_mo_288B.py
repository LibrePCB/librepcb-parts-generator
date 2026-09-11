"""
This file contains configurations for QFN packages according to MO-228B
Not all possible combinations are generated. You can enable more combinations in the table below.
"""

from dataclasses import dataclass, field

from typing import Optional

from qfn_common import Size, Variant, qfn_name

# table 1 values
overall_heights = dict(
    U=0.65,
    X1=0.50,
    X2=0.40,
)

body_lengths = dict(
    A=1.00,
    B=1.10,
    C=1.20,
    D=1.40,
    E=1.50,
    F=1.80,
    G=2.00,
    H=2.30,
    J=2.50,
    K=2.20,
)

body_size_ys = dict(
    A=1.00,
    B=1.40,
    C=1.50,
    D=1.70,
    E=1.80,
    F=2.00,
    G=2.10,
    H=2.60,
    J=2.80,
    K=3.00,
    L=3.40,
    M=1.20,
)

terminal_pitches = dict(
    D=0.50,
    E=0.40,
    F=0.35,
)

# table 3
lead_widths = {
    0.50: 0.25,
    0.40: 0.20,
    0.35: 0.17,
}


@dataclass
class VariantRow:
    tag: Optional[str]
    e: float
    D: float
    E: float
    D2: Optional[float]
    E2: Optional[float]
    L: float
    L1: Optional[float]
    ND: int
    NE: int
    names: list[tuple[str, str]] = field(default_factory=list)


# table 6
# other values are derived from variation designators
# fmt: off
variant_table_definition = [
    #           tag      e     D     E     D2    E2    L     L1   ND NE
    VariantRow('xECD  ', 0.50, 1.50, 1.50, None, None, 0.35, 0.40, 1, 3), # smallest
    VariantRow('xHJF  ', 0.35, 2.30, 2.80, None, None, 0.30, 0.40, 4, 8), # biggest
    VariantRow(  None  , 0.40, 3.00, 3.00, 1.90, 1.90, 0.35, 0.35, 5, 5, names=[('SOT1969-1', 'NXP')]),
]
# fmt: on


# table 2
min_K = 0.15


def load_variants() -> list[Variant]:
    variants: list[Variant] = []
    for row in variant_table_definition:
        body_size_y = row.E
        body_size_x = row.D
        pitch = row.e
        if row.tag:
            tag = row.tag.strip()
            length_code = tag[1]
            width_code = tag[2]
            pitch_code = tag[3]
            assert body_size_ys[width_code] == body_size_y
            assert body_lengths[length_code] == body_size_x
            assert terminal_pitches[pitch_code] == pitch
        lead_width = lead_widths[pitch]
        num_pins = 2 * row.ND + 2 * row.NE
        L1 = row.L1 if row.L1 else row.L
        exposed_pad = Size(x=row.D2, y=row.E2) if row.D2 and row.E2 else None
        for height_code in ('U',):  # We ignore X1 and X2 because the height difference is minimal
            if row.D2 and row.E2:
                assert row.D >= 2 * row.L + 2 * min_K + row.D2, row
                assert row.E >= 2 * L1 + 2 * min_K + row.E2, row
            else:
                assert not row.D2 and not row.E2, 'D2 and E2 must be defined as a pair'
            overall_height = overall_heights[height_code]
            variants.append(
                Variant(
                    standard='MO-288B',
                    name=qfn_name(
                        standard=f'H{height_code}F-PQFN',
                        num_pins=num_pins,
                        pitch=pitch,
                        body_length=body_size_x,
                        body_width=body_size_x,
                        body_height=overall_height,
                        lead_length=row.L,
                        lead_width=lead_width,
                        exposed_pad=exposed_pad,
                    ),
                    overall_height=overall_height,
                    body_size_x=body_size_x,
                    body_size_y=body_size_y,
                    pitch=pitch,
                    # upper_body_size_y=row.D1,
                    # upper_body_size_x=row.E1,
                    exposed_pad=exposed_pad,
                    lead_length_east_west=row.L,
                    lead_length_north_south=L1,
                    lead_width=lead_width,
                    num_pins_north_south=row.ND,
                    num_pins_east_west=row.NE,
                    min_clearance=min_K,
                    alternative_names=row.names,
                )
            )
    return variants
