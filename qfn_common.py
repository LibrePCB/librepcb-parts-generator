from dataclasses import dataclass, field

from common import format_ipc_dimension as fp


@dataclass(frozen=True)
class Size:
    x: float
    y: float


def qfn_name(
    standard: str,
    num_pins: int,
    pitch: float,
    body_length: float,
    body_width: float,
    body_height: float,
    lead_length: float,
    lead_width: float,
    exposed_pad: Size | None,
) -> str:
    # Footprint expert guideline p.42: "Thermal Tabs are included in the Pin Quantity"
    naming_num_pins = num_pins + (1 if exposed_pad else 0)
    exposed = f'T{fp(exposed_pad.y)}X{fp(exposed_pad.x)}' if exposed_pad else ''
    return (
        f'{standard}{naming_num_pins}P{fp(pitch)}_'
        + f'{fp(body_length)}X{fp(body_width)}X{fp(body_height)}L{fp(lead_length)}X{fp(lead_width)}{exposed}'
    )


@dataclass(frozen=True)
class Variant:
    name: str
    standard: str
    overall_height: float
    body_size_x: float
    body_size_y: float
    pitch: float
    # only for rendering, unused because we don't differentiate between different package versions
    # upper_body_size_x: float
    # upper_body_size_y: float
    exposed_pad: Size | None
    lead_length_east_west: float
    lead_length_north_south: float
    lead_width: float
    num_pins_east_west: int
    num_pins_north_south: int
    min_clearance: float
    alternative_names: list[tuple[str, str]]
    # relative to "lead width / 2", e.g. the default gives R=0.05 for a lead width of 0.25
    pad_radius: float = field(default=0.4)

    @property
    def num_pins(self) -> int:
        return 2 * (self.num_pins_east_west + self.num_pins_north_south)
