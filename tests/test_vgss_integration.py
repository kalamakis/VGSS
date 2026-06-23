from pathlib import Path

import numpy as np

from bgs.matlab_parser import parse_matlab_geometry
from bgs.sampling import sample_on_vgss
from bgs.topology import find_touching_nets
from bgs.vgss import build_all_net_vgss, build_vgss_for_conductor
from bgs.vgss_geometry import classify_candidate, faces_containing_point
from bgs.visualization import plot_vgss_results


def _assert_point_is_valid_for_net(net_vgss, point: np.ndarray) -> None:
    """Check an accepted point using the same geometry rules as Algorithm 4.1."""

    source_index = next(
        index
        for index, surface in enumerate(net_vgss.surfaces)
        if faces_containing_point(surface, point)
    )
    source_face = faces_containing_point(
        net_vgss.surfaces[source_index],
        point,
    )[0]
    classification = classify_candidate(
        net_vgss.surfaces,
        source_index,
        source_face,
        point,
        neighbor_indices=net_vgss.sampling_context.neighbor_lists[source_index],
    )
    assert classification.is_geometrically_valid


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
    _assert_point_is_valid_for_net(net_vgss, point)


def test_build_all_net_vgss_builds_and_samples_every_detected_net() -> None:
    path = Path(__file__).parents[1] / "input" / "INPUTFILE_TOUCHING_DIRECT.m"
    conductors = parse_matlab_geometry(path)

    all_net_vgss = build_all_net_vgss(
        conductors,
        scale_factor=1.0,
        max_distance=10.0,
    )

    assert [item.net.conductor_names for item in all_net_vgss] == [
        ("C1", "C2", "C3"),
        ("C4",),
        ("C5",),
    ]
    assert [len(item.surfaces) for item in all_net_vgss] == [3, 1, 1]

    # Each net-level VGSS contains exactly one BGS per conductor in that net.
    for item in all_net_vgss:
        assert tuple(
            surface.master_conductor for surface in item.surfaces
        ) == item.net.conductor_names

    rng = np.random.default_rng(1234)
    sampled_points: dict[str, np.ndarray] = {}

    for item in all_net_vgss:
        points = np.vstack(
            [sample_on_vgss(item.sampling_context, rng) for _ in range(25)]
        )
        sampled_points[item.net.name] = points
        assert points.shape == (25, 3)
        for point in points:
            _assert_point_is_valid_for_net(item, point)

    assert set(sampled_points) == {"Net1", "Net2", "Net3"}


def test_all_net_vgss_visualization_is_saved(tmp_path: Path) -> None:
    path = Path(__file__).parents[1] / "input" / "INPUTFILE_TOUCHING_DIRECT.m"
    conductors = parse_matlab_geometry(path)
    all_net_vgss = build_all_net_vgss(conductors)

    rng = np.random.default_rng(2026)
    sampled_points = {
        item.net.name: np.vstack(
            [sample_on_vgss(item.sampling_context, rng) for _ in range(10)]
        )
        for item in all_net_vgss
    }

    output_path = tmp_path / "all_net_vgss.png"
    plot_vgss_results(
        conductors,
        all_net_vgss,
        sampled_points,
        save_path=output_path,
        show=False,
    )

    assert output_path.is_file()
    assert output_path.stat().st_size > 0
