from __future__ import annotations

import numpy as np
import pytest

from bgs.models import Bounds, GaussianSurface, make_surface_faces
from bgs.sampling import prepare_vgss_sampling, sample_on_vgss
from bgs.vgss_geometry import point_on_surface


class ScriptedRNG:
    """Minimal deterministic RNG used to force Algorithm 4.1 branches."""

    def __init__(self, choices: list[int], random_values: list[list[float]]):
        self._choices = iter(choices)
        self._random_values = iter(random_values)

    def choice(self, _count: int, p=None) -> int:
        return next(self._choices)

    def random(self, size=None):
        values = np.asarray(next(self._random_values), dtype=float)
        if size is None:
            return float(values[0])
        assert values.shape == (size,)
        return values


def surface(name: str, bounds: Bounds) -> GaussianSurface:
    return GaussianSurface(name, bounds, make_surface_faces(bounds))


def test_single_bgs_returns_a_surface_point() -> None:
    only_surface = surface("C1", Bounds(0, 1, 0, 2, 0, 3))
    context = prepare_vgss_sampling([only_surface])
    rng = np.random.default_rng(1234)

    point = sample_on_vgss(context, rng)

    assert point.shape == (3,)
    assert point_on_surface(only_surface, point)


def test_internal_opposite_face_is_rejected_before_external_face_is_returned() -> None:
    left = surface("A", Bounds(0, 1, 0, 1, 0, 1))
    right = surface("B", Bounds(1, 2, 0, 1, 0, 1))
    context = prepare_vgss_sampling([left, right])

    # Attempt 1: choose A/PX at its center -> shared internal face, rejected.
    # Attempt 2: choose A/NX at its center -> external face, accepted.
    rng = ScriptedRNG(
        choices=[0, 0, 0, 3],
        random_values=[
            [0.5, 0.5],
            [0.5, 0.5],
            [0.2, 0.2],
        ],
    )

    point = sample_on_vgss(context, rng)

    assert np.allclose(point, [0.0, 0.5, 0.5])


def test_nc_correction_can_reject_then_accept_identical_surfaces() -> None:
    first = surface("A", Bounds(0, 1, 0, 1, 0, 1))
    second = surface("B", Bounds(0, 1, 0, 1, 0, 1))
    context = prepare_vgss_sampling([first, second])

    # Both attempts choose A/PX at the center.  n_c = 2.
    # First x1=0.75 rejects; second x1=0.25 accepts.
    rng = ScriptedRNG(
        choices=[0, 0, 0, 0],
        random_values=[
            [0.5, 0.5],
            [0.75, 0.1],
            [0.5, 0.5],
            [0.25, 0.1],
        ],
    )

    point = sample_on_vgss(context, rng)

    assert np.allclose(point, [1.0, 0.5, 0.5])


def test_importance_function_is_configurable() -> None:
    only_surface = surface("C1", Bounds(0, 1, 0, 1, 0, 1))
    context = prepare_vgss_sampling(
        [only_surface],
        importance_function=lambda _point: 2.0,
        upper_bound=1.0,
    )

    with pytest.raises(ValueError, match="exceeds U"):
        sample_on_vgss(context, np.random.default_rng(1))

class ProbabilityCaptureRNG:
    def __init__(self):
        self.probabilities = None

    def choice(self, _count: int, p=None) -> int:
        self.probabilities = np.asarray(p, dtype=float)
        return 0


def test_bgs_selection_probabilities_are_proportional_to_area() -> None:
    from bgs.sampling import choose_surface_index_by_area

    first = surface("A", Bounds(0, 1, 0, 1, 0, 1))  # area 6
    second = surface("B", Bounds(0, 2, 0, 1, 0, 1))  # area 10
    rng = ProbabilityCaptureRNG()

    choose_surface_index_by_area([first, second], rng)

    assert np.allclose(rng.probabilities, [6 / 16, 10 / 16])


def test_face_selection_probabilities_are_proportional_to_area() -> None:
    from bgs.sampling import choose_face_index_by_area

    cuboid = surface("A", Bounds(0, 1, 0, 2, 0, 3))
    rng = ProbabilityCaptureRNG()

    choose_face_index_by_area(cuboid, rng)

    # Face order: PX, PY, PZ, NX, NY, NZ.
    assert np.allclose(rng.probabilities, np.asarray([6, 3, 2, 6, 3, 2]) / 22)
