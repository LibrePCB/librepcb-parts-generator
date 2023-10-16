"""
Generate only the 3D models for TO-92
"""
from os import path

import cadquery as cq

from cadquery_helpers import StepAssembly, StepColor, StepConstants


def generate_leg_path(plane: str, length: float, delta: float) -> cq.Workplane:
    straight_length = 1
    return cq.Workplane(plane) \
        .vLine(length - straight_length - abs(delta)) \
        .line(-delta, abs(delta)) \
        .vLine(straight_length)


def generate(
    name: str,
    pitch_x: float,
    pitch_y: float,
) -> None:
    print(f'Generating pkg 3D model "{name}"')

    body_standoff = 3.0
    body_height = 5.0
    body_diameter = 5.1
    body_edge = -1.65
    leg_width = 0.45
    leg_z = -StepConstants.THT_LEAD_SOLDER_LENGTH
    leg_length = StepConstants.THT_LEAD_SOLDER_LENGTH + body_standoff + 0.1

    body = cq.Workplane('XY', origin=(0, 0, body_standoff)) \
        .cylinder(body_height, body_diameter / 2, centered=(True, True, False)) \
        .fillet(0.3) \
        .moveTo(0, body_edge - 10) \
        .box(20, 10, 50, centered=(True, False, False), combine='cut')

    leg_straight = cq.Workplane('XY', origin=(0, 0, leg_z)) \
        .box(leg_width, leg_width, leg_length, centered=(True, True, False))
    if pitch_x == 1.27:
        leg_1 = leg_straight
        leg_3 = leg_straight
    else:
        leg_1 = cq.Workplane('XY') \
            .rect(leg_width, leg_width) \
            .sweep(generate_leg_path('XZ', leg_length, -pitch_x + 1.27)) \
            .translate((-pitch_x + 1.27, 0, leg_z))
        leg_3 = cq.Workplane('XY') \
            .rect(leg_width, leg_width) \
            .sweep(generate_leg_path('XZ', leg_length, pitch_x - 1.27)) \
            .translate((pitch_x - 1.27, 0, leg_z))
    if pitch_y == 0:
        leg_2 = leg_straight
    else:
        leg_2 = cq.Workplane('XY') \
            .rect(leg_width, leg_width) \
            .sweep(generate_leg_path('YZ', leg_length, pitch_y)) \
            .translate((0, pitch_y, leg_z))

    assembly = StepAssembly(name)
    assembly.add_body(body, 'body', StepColor.IC_BODY)
    assembly.add_body(
        leg_1, 'leg-1', StepColor.LEAD_SMT,
        location=cq.Location((-1.27, 0, 0))
    )
    assembly.add_body(
        leg_2, 'leg-2', StepColor.LEAD_SMT,
        location=cq.Location((0, 0, 0))
    )
    assembly.add_body(
        leg_3, 'leg-3', StepColor.LEAD_SMT,
        location=cq.Location((1.27, 0, 0))
    )

    out_path = path.join('out_3d', 'to92', f'{name}.step')
    assembly.save(out_path, fused=True)


if __name__ == '__main__':
    generate(name='Straight', pitch_x=1.27, pitch_y=0)
    generate(name='Zigzag', pitch_x=1.27, pitch_y=1.27)
    generate(name='Wide', pitch_x=2.54, pitch_y=0)
