"""
This file contains configurations for QFN packages according to MO-220-K.01.
Not all possible combinations are generated. You can enable more combinations in the table below.
"""

from dataclasses import dataclass, field

from typing import Optional

from qfn_common import Size, Variant, qfn_name

# table 1 values
overall_heights = dict(
    V=1.00,
    W=0.80,
)

# body length/width have the same assignment
body_size = dict(
    A=1.0,
    B=1.5,
    C=2.0,
    D=2.5,
    E=3.0,
    F=3.5,
    G=4.0,
    H=5.0,
    J=6.0,
    K=7.0,
    L=8.0,
    M=9.0,
    N=10.0,
    P=11.0,
    R=12.0,
    S=4.5,
    T=5.5,
    U=6.5,
)

terminal_pitch = dict(
    A=1.00,
    B=0.80,
    C=0.65,
    D=0.50,
    E=0.40,
)

# table 3
lead_widths = {
    1.00: 0.40,
    0.80: 0.30,
    0.65: 0.30,
    0.50: 0.25,
    0.40: 0.20,
}


@dataclass
class VariantRow:
    tag: str
    e: float
    D: float
    E: float
    D1: Optional[float]
    E1: Optional[float]
    D2: float
    E2: float
    L: float
    ND: int
    NE: int
    names: list[tuple[str, str]] = field(default_factory=list)


# table 6
# other values are derived from variation designators
# fmt: off
variant_table_definition = [
    #           tag      e      D      E      D1     E1     D2     E2    L     ND  NE
    VariantRow('xEEB  ', 0.80,  3.00,  3.00,  2.75,  2.75,  0.70,  0.70, 0.55,  1,  1), # smallest
    VariantRow('xRRE-2', 0.40, 12.00, 12.00, 11.75, 11.75, 10.10, 10.10, 0.40, 27, 27), # biggest
    VariantRow('xGGD-9', 0.50,  4.00,  4.00,  None,  None,  2.45,  2.45, 0.50,  6,  6, names=[('RGE0024B', 'TI'), ('SOT616-1', 'NXP')]), # noqa: E501
    VariantRow('xGGD-6', 0.50,  4.00,  4.00,  None,  None,  2.65,  2.80, 0.40,  6,  6, names=[('SOT616-3', 'NXP')]),
]
# fmt: on


min_K = 0.20


def load_variants() -> list[Variant]:
    variants: list[Variant] = []
    for row in variant_table_definition:
        length_code = row.tag[1]
        width_code = row.tag[2]
        pitch_code = row.tag[3]
        body_size_y = body_size[width_code]
        body_size_x = body_size[length_code]
        pitch = terminal_pitch[pitch_code]
        assert body_size_x == row.D
        assert body_size_y == row.E
        assert pitch == row.e
        num_pins = 2 * row.ND + 2 * row.NE
        exposed_pad = Size(x=row.D2, y=row.E2) if row.D2 and row.E2 else None
        lead_length = row.L
        lead_width = lead_widths[terminal_pitch[pitch_code]]
        for height_code in ('V',):  # we ignore 'W' to have less packages
            assert row.D >= 2 * row.L + 2 * min_K + row.D2, row
            assert row.E >= 2 * row.L + 2 * min_K + row.E2, row
            overall_height = overall_heights[height_code]
            variants.append(
                Variant(
                    standard='MO-220-K.01',
                    name=qfn_name(
                        standard=f'H{height_code}F-PQFN',
                        num_pins=num_pins,
                        pitch=pitch,
                        body_length=body_size_y,
                        body_width=body_size_x,
                        body_height=overall_height,
                        lead_length=lead_length,
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
                    lead_length_east_west=lead_length,
                    lead_length_north_south=lead_length,
                    lead_width=lead_width,
                    num_pins_north_south=row.ND,
                    num_pins_east_west=row.NE,
                    min_clearance=min_K,
                    alternative_names=row.names,
                )
            )
    return variants
