from pathlib import Path

import pytest

from bgs.gaussian_surface import (
    UnsupportedGeometryError,
    generate_bgs,
)
from bgs.matlab_parser import parse_matlab_geometry
from bgs.models import Bounds, Conductor
import numpy as np


def test_only_directly_touching_blocks_are_ignored() -> None:
    faces = np.zeros((6, 4, 3), dtype=float)
    c1 = Conductor(
        "C1",
        Bounds(0, 1, 0, 1, 0, 1),
        faces,
    )
    # Directly touches C1: ignored.
    c2 = Conductor(
        "C2",
        Bounds(1, 2, 0, 1, 0, 1),
        faces,
    )
    # Touches C2, but does not directly touch C1.
    # It must still constrain the BGS around C1.
    c3 = Conductor(
        "C3",
        Bounds(2, 3, 0, 1, 0, 1),
        faces,
    )
    result = generate_bgs(
        c1,
        [c1, c2, c3],
        scale_factor=1,
    )

    assert result is not None

    # C2 is ignored.
    # C3 remains relevant:
    # dPX(C1, C3) = 2 - 1 = 1
    # Initial BGS distance = 1 / 2 = 0.5
    assert result.initial_extents["PX"] == 0.5


def test_c1_surface_with_scale_factor_two() -> None:
    path = Path(__file__).parents[1] / "input" / "INPUTFILE_05.m"
    conductors = parse_matlab_geometry(path)
    c1 = next(item for item in conductors if item.name == "C1")

    result = generate_bgs(c1, conductors, scale_factor=2)
    assert result is not None

    assert result.initial_extents["PX"] == 1
    assert result.initial_extents["PY"] == 1

    assert result.final_extents == {
        "PX": 1,
        "PY": 1,
        "PZ": 2,
        "NX": 2,
        "NY": 2,
        "NZ": 2,
    }

    assert result.gaussian_surface.bounds == Bounds(-2, 2, -2, 2, -2, 3)


# def test_touching_distinct_blocks_can_raise_clear_error() -> None:
#     faces = np.zeros((6, 4, 3), dtype=float)
#     c1 = Conductor("C1", Bounds(0, 1, 0, 1, 0, 1), faces)
#     c2 = Conductor("C2", Bounds(1, 2, 0, 1, 0, 1), faces)

#     with pytest.raises(UnsupportedGeometryError):
#         generate_bgs(c1, [c1, c2], touch_policy="error")
