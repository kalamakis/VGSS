from pathlib import Path

import numpy as np

from bgs.matlab_parser import parse_matlab_geometry
from bgs.sampling import sample_on_vgss
from bgs.topology import find_touching_nets
from bgs.vgss import build_vgss_for_conductor
from bgs.vgss_geometry import classify_candidate, faces_containing_point


def test_touching_input_builds_one_vgss_for_c1_c2_c3() -> None:
    path = Path(__file__).parents[1] / "input" / "INPUTFILE_TOUCHING_DIRECT.m"
    conductors = parse_matlab_geometry(path)

    nets = find_touching_nets(conductors)
    assert [net.conductor_names for net in nets] == [
        ("C1", "C2", "C3"),
        ("C4",),
        ("C5",),
    ]

    net_vgss = build_vgss_for_conductor(
        conductors,
        "C1",
        scale_factor=1.0,
        max_distance=10.0,
    )

    assert net_vgss.net.conductor_names == ("C1", "C2", "C3")
    assert len(net_vgss.surfaces) == 3

    rng = np.random.default_rng(7)
    point = sample_on_vgss(net_vgss.sampling_context, rng)

    # The accepted point must be on at least one BGS and must pass the same
    # geometric checks used by Algorithm 4.1.
    source_index = next(
        index
        for index, surface in enumerate(net_vgss.surfaces)
        if faces_containing_point(surface, point)
    )
    source_face = faces_containing_point(net_vgss.surfaces[source_index], point)[0]
    classification = classify_candidate(
        net_vgss.surfaces,
        source_index,
        source_face,
        point,
        neighbor_indices=net_vgss.sampling_context.neighbor_lists[source_index],
    )
    assert classification.is_geometrically_valid
