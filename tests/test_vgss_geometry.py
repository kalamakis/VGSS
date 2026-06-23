import numpy as np

from bgs.models import Bounds, GaussianSurface, make_surface_faces
from bgs.vgss_geometry import (
    build_neighbor_lists,
    classify_candidate,
    point_strictly_inside_bounds,
)


def surface(name: str, bounds: Bounds) -> GaussianSurface:
    return GaussianSurface(name, bounds, make_surface_faces(bounds))


def face(surface_: GaussianSurface, direction: str):
    return next(item for item in surface_.faces if item.direction == direction)


def test_point_strictly_inside_excludes_boundary() -> None:
    bounds = Bounds(0, 1, 0, 1, 0, 1)

    assert point_strictly_inside_bounds(np.array([0.5, 0.5, 0.5]), bounds)
    assert not point_strictly_inside_bounds(np.array([1.0, 0.5, 0.5]), bounds)


def test_candidate_inside_another_bgs_is_rejected() -> None:
    source = surface("A", Bounds(0, 1, 0, 1, 0, 1))
    enclosing = surface("B", Bounds(0.5, 1.5, -1, 2, -1, 2))
    point = np.array([1.0, 0.5, 0.5])

    result = classify_candidate(
        [source, enclosing],
        0,
        face(source, "PX"),
        point,
    )

    assert result.inside_other_surface
    assert not result.is_geometrically_valid


def test_opposite_normal_shared_face_is_rejected() -> None:
    left = surface("A", Bounds(0, 1, 0, 1, 0, 1))
    right = surface("B", Bounds(1, 2, 0, 1, 0, 1))
    point = np.array([1.0, 0.5, 0.5])

    result = classify_candidate(
        [left, right],
        0,
        face(left, "PX"),
        point,
    )

    assert result.has_opposite_normal
    assert not result.is_geometrically_valid


def test_identical_external_surfaces_have_multiplicity_two() -> None:
    first = surface("A", Bounds(0, 1, 0, 1, 0, 1))
    second = surface("B", Bounds(0, 1, 0, 1, 0, 1))
    point = np.array([1.0, 0.5, 0.5])

    result = classify_candidate(
        [first, second],
        0,
        face(first, "PX"),
        point,
    )

    assert result.is_geometrically_valid
    assert result.coincident_surface_count == 2


def test_neighbor_lists_include_only_intersecting_bgs() -> None:
    first = surface("A", Bounds(0, 1, 0, 1, 0, 1))
    second = surface("B", Bounds(1, 2, 0, 1, 0, 1))
    third = surface("C", Bounds(5, 6, 5, 6, 5, 6))

    assert build_neighbor_lists([first, second, third]) == ((1,), (0,), ())
