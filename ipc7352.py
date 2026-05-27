import math
from dataclasses import dataclass
from typing import Optional

# From JEDEC MS-012
W_min = 0.31  # min lead width
W_max = 0.51  # max lead width
L_min = 6.0  # min lead span
L_max = 6.0  # max lead span
T_min = 0.835 - 0.435  # min contact length
T_max = 0.835 + 0.435  # max contact length

# Intermediate Values
W_tol = W_max - W_min
L_tol = L_max - L_min
S_max = L_max - (2 * T_min)
S_min = L_min - (2 * T_max)
S_tol = S_max - S_min
T_tol = T_max - T_min

@dataclass(frozen=True)
class IpcSolderJointTable:
    toe: float
    heel: float
    side: float
    courtyard: float


class IpcPackageDimension:
    def __init__(self, min: float, max: float):
        self.min = min
        self.max = max
        self.tolerance = self.max - self.min
        self.is_nominal = self.min == self.max
        assert self.min <= self.max

    @classmethod
    def nominal(cls, value: float, plusminus: float = 0) -> cls:
        return cls(value - plusminus, value + plusminus)


@dataclass(frozen=True)
class IpcCalculatorResult:
    pad_pos_dx: float
    pad_size_x: float
    pad_size_y: float


class IpcCalculator:
    def __init__(self, lead_span: IpcPackageDimension, terminal_length: IpcPackageDimension, lead_space: Optional[IpcPackageDimension], lead_width: IpcPackageDimension, fabrication_tolerance: float = 0.0, placement_tolerance: float = 0.0):
        self.lead_span = lead_span
        self.terminal_length = terminal_length
        if lead_space is None:
            self.lead_space = IpcPackageDimension(
                min=self.lead_span.min - 2 * self.terminal_length.max,
                max=self.lead_span.max - 2 * self.terminal_length.min,
            )
        else:
            self.lead_space = lead_space
        self.lead_width = lead_width
        self.fabrication_tolerance = fabrication_tolerance
        self.placement_tolerance = placement_tolerance
        assert self.lead_space.max < self.lead_span.min
        assert self.terminal_length.max < (self.lead_span.min / 2)

    def calculate(self, table: IpcSolderJointTable) -> IpcCalculatorResult:
        toe_tolerance = math.sqrt(math.pow(self.lead_span.tolerance, 2) + math.pow(2 * self.fabrication_tolerance, 2) + math.pow(2 * self.placement_tolerance, 2))  # Tt
        pad_span = self.lead_span.min + (2 * table.toe) + toe_tolerance  # Zmax
        lead_space_tolerance_rms = math.sqrt(math.pow(self.lead_span.tolerance, 2) + 2 * math.pow(self.terminal_length.tolerance, 2))  # Stol(RMS)
        lead_space_difference = self.lead_space.tolerance - lead_space_tolerance_rms  # Sdiff
        lead_space_rms = IpcPackageDimension(
            min=self.lead_space.min + (lead_space_difference / 2),  # Smin(RMS)
            max=self.lead_space.max - (lead_space_difference / 2),  # Smax(RMS)
        )
        heel_tolerance = math.sqrt(math.pow(lead_space_rms.max - lead_space_rms.min, 2) + math.pow(2 * self.fabrication_tolerance, 2) + math.pow(2 * self.placement_tolerance, 2))  # Ht
        pad_space = lead_space_rms.max - (2 * table.heel) - heel_tolerance  # Gmin
        pad_size_x = (pad_span - pad_space) / 2
        return IpcCalculatorResult(
            pad_pos_dx=(pad_span - pad_size_x) / 2,
            pad_size_x=pad_size_x,
            pad_size_y=self.lead_width.max + (2 * table.side),
        )


calculator = IpcCalculator(
    lead_span=IpcPackageDimension.nominal(6.0),
    terminal_length=IpcPackageDimension.nominal(0.835, 0.435),
    lead_space=None,
    lead_width=IpcPackageDimension(0.31, 0.51),
)


# Density Levels (pitch > 1.00mm)
DENSITY_LEVELS = [
    dict(name="Least Density Level", table=IpcSolderJointTable(toe=0.3, heel=0.4, side=0.06, courtyard=None)),
    dict(name="Nominal Density Level", table=IpcSolderJointTable(toe=0.35, heel=0.5, side=0.08, courtyard=None)),
    dict(name="Most Density Level", table=IpcSolderJointTable(toe=0.4, heel=0.6, side=0.1, courtyard=None)),
]

# Fabrication Tolerances
F = 0.0
P = 0.0

for lvl in DENSITY_LEVELS:
    print(lvl["name"])

    res = calculator.calculate(lvl["table"])

    # Pad Size X
    T_t = math.sqrt(math.pow(L_tol, 2) + math.pow(2 * F, 2) + math.pow(2 * P, 2))
    Z_max = L_min + (2 * lvl["table"].toe) + T_t
    S_tol_rms = math.sqrt(math.pow(L_tol, 2) + 2 * math.pow(T_tol, 2))
    S_diff = S_tol - S_tol_rms
    S_max_rms = S_max - (S_diff / 2)
    S_min_rms = S_min + (S_diff / 2)
    H_t = math.sqrt(math.pow(S_max_rms - S_min_rms, 2) + math.pow(2 * F, 2) + math.pow(2 * P, 2))
    G_min = S_max_rms - (2 * lvl["table"].heel) - H_t
    pad_size_x = (Z_max - G_min) / 2

    # Pad Size Y
    pad_size_y = W_min + (2 * lvl["table"].side) + W_tol

    # Pad center-to-center
    pad_dx = (Z_max - pad_size_x) / 2

    # Result
    #print(f"  Z_max = {round(Z_max, 2)}")
    #print(f"  G_min = {round(G_min, 2)}")
    print(f"  pad_size_x = {round(res.pad_size_x, 2)}")
    print(f"  pad_size_y = {round(res.pad_size_y, 2)}")
    print(f"  pad_dx = {round(res.pad_pos_dx, 2)}")
