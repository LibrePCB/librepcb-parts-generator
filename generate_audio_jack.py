"""
Generate only the 3D models for audio jacks
"""

from os import path

import cadquery as cq

from cadquery_helpers import StepAssembly, StepColor


def generate_samesky_sj6306(
    name: str,
    ring: bool,
    tip_switch: bool,
) -> None:
    print(f'Generating pkg 3D model "{name}"')

    assembly = StepAssembly(name)

    body = (
        cq.Workplane('XY', origin=(0, 0, 0))
        .box(10.0, 25.0, 12.5, centered=(True, True, False))
        .workplane(origin=(0, 10.0))
        .box(14.0, 2.5, 12.5, centered=(True, False, True))
        .faces('>Y')
        .workplane(offset=-1)
        .cylinder(10.0, 5.2, centered=(True, True, False))
        .faces('>Y')
        .workplane(offset=1)
        .cylinder(31.0, 3.2, centered=(True, True, True), combine='cut')
    )
    assembly.add_body(body, 'body', StepColor.IC_BODY)

    lead = cq.Workplane('XY', origin=(0, 0, -4.0)).box(0.5, 2.0, 4.0, centered=(True, True, False))
    assembly.add_body(lead, 'lead-1', StepColor.LEAD_THT, location=cq.Location((0.0, 5.0, 0.0)))
    assembly.add_body(lead, 'lead-2', StepColor.LEAD_THT, location=cq.Location((-2.5, -9.9, 0.0)))
    if ring:
        assembly.add_body(
            lead, 'lead-3', StepColor.LEAD_THT, location=cq.Location((2.5, -9.9, 0.0))
        )
    if tip_switch:
        assembly.add_body(
            lead, 'lead-4', StepColor.LEAD_THT, location=cq.Location((-2.5, -2.7, 0.0))
        )

    # Save without fusing for massively better minification!
    out_path = path.join('out_3d', 'audio_jack', f'{name}.step')
    assembly.save(out_path, fused=False)


if __name__ == '__main__':
    # Same Sky SJ-6306
    # https://www.sameskydevices.com/product/resource/sj-6306.pdf
    generate_samesky_sj6306(name='SJ-63062A', ring=False, tip_switch=False)
    generate_samesky_sj6306(name='SJ-63062B', ring=False, tip_switch=True)
    generate_samesky_sj6306(name='SJ-63063B', ring=True, tip_switch=True)
