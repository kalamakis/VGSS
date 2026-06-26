from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from FRW.random_walk import run_frw_geometry
from bgs.matlab_parser import parse_matlab_geometry
from bgs.models import Bounds, GaussianSurface, make_surface_faces
from bgs.sampling import VGSSSamplingStats, prepare_vgss_sampling, sample_on_vgss
from bgs.vgss import build_vgss_for_conductor


def _surface(name: str, bounds: Bounds) -> GaussianSurface:
    return GaussianSurface(name, bounds, make_surface_faces(bounds))


def test_sampling_stats_return_area_when_p_is_one() -> None:
    surface = _surface("C1", Bounds(0, 1, 0, 2, 0, 3))
    context = prepare_vgss_sampling([surface])
    stats = VGSSSamplingStats()
    rng = np.random.default_rng(11)

    for _ in range(25):
        sample_on_vgss(context, rng, stats=stats)

    assert stats.proposal_count == 25
    assert stats.accepted_count == 25
    assert stats.estimate_H(context) == pytest.approx(surface.area)


def test_sampling_stats_estimate_weighted_H() -> None:
    surface = _surface("C1", Bounds(0, 1, 0, 1, 0, 1))
    context = prepare_vgss_sampling(
        [surface],
        importance_function=lambda _point: 0.5,
        upper_bound=1.0,
    )
    stats = VGSSSamplingStats()
    rng = np.random.default_rng(2026)

    for _ in range(4000):
        sample_on_vgss(context, rng, stats=stats)

    assert stats.estimate_H(context) == pytest.approx(3.0, rel=0.04)
    assert stats.importance_rejections > 0


def test_frw_batch_keeps_original_walk_shape_and_uses_vgss_start() -> None:
    input_path = Path(__file__).parents[1] / "input" / "INPUTFILE_TOUCHING_DIRECT.m"
    conductors = parse_matlab_geometry(input_path)
    master_vgss = build_vgss_for_conductor(
        conductors,
        "C1",
        scale_factor=1.0,
        max_distance=10.0,
    )

    result = run_frw_geometry(
        conductors,
        master_vgss,
        np.random.default_rng(1234),
        num_walks=8,
        max_hops=8,
    )

    assert len(result["walks"]) == 8
    assert result["sampling_stats"]["accepted_count"] == 8
    assert result["sampling_stats"]["proposal_count"] >= 8
    assert result["H"] == result["sampling_stats"]["H_estimate"]

    for walk in result["walks"]:
        assert len(walk["start_point"]) == 3
        assert "path_data" in walk
        assert "hit_conductor" in walk
        for hop in walk["path_data"]:
            assert set(hop) == {"center", "a"}
