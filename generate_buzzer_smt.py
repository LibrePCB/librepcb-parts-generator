"""
Generate only the 3D models for SMT buzzers
"""

from os import path

import cadquery as cq

from cadquery_helpers import StepAssembly


def generate(
    name: str,
    body_width: float,
    body_length: float,
    body_height: float,
    body_chamfer: float,
    body_color: cq.Color,
    hole_diameter: float,
    hole_depth: float,
) -> None:
    print(f'Generating pkg 3D model "{name}"')

    assembly = StepAssembly(name)

    body = (
        cq.Workplane('XY', origin=(0, 0, body_height / 2))
        .box(body_width, body_length, body_height)
        .edges('|Z')
        .chamfer(body_chamfer)
        .edges()
        .chamfer(0.1)
    )
    body = body.workplane(origin=(0, 0), offset=body_height / 2).cylinder(
        hole_depth * 2, hole_diameter / 2, centered=(True, True, True), combine='cut'
    )
    assembly.add_body(body, 'body', body_color)

    membran = cq.Workplane('XY', origin=(0, 0, body_height - hole_depth)).cylinder(
        0.2, hole_diameter / 2
    )
    assembly.add_body(membran, 'membran', cq.Color('gainsboro'))

    pads_height = 0.2
    pads = cq.Workplane('XY', origin=(0, 0, 0.02 + pads_height / 2)).box(
        body_width - 0.2, body_length - 0.2, pads_height
    )
    assembly.add_body(pads, 'pads', cq.Color('burlywood'))

    # Save without fusing for massively better minification!
    out_path = path.join('out_3d', 'buzzer', f'{name}.step')
    assembly.save(out_path, fused=False)


if __name__ == '__main__':
    # CUI CSS-I4B20-SMT-TR
    # https://www.sameskydevices.com/product/resource/css-i4b20-smt-tr.pdf
    generate(
        name='CSS-I4B20-SMT-TR',
        body_width=8.7,  # 8.5 according datasheet, but real device has ~8.8mm
        body_length=8.7,  # 8.5 according datasheet, but real device has ~8.8mm
        body_height=3.0,
        body_chamfer=1.5,
        body_color=cq.Color('beige'),
        hole_diameter=5.0,  # measured from real device
        hole_depth=0.8,  # measured from real device
    )
