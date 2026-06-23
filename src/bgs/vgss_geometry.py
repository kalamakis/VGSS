from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math

import numpy as np

from .models import Bounds, GaussianSurface, SurfaceFace


@dataclass(frozen=True)
class CandidateClassification:
    """Geometric result for one proposed Algorithm 4.1 point."""

    inside_other_surface: bool
    has_opposite_normal: bool
    coincident_surface_count: int

    @property
    def is_geometrically_valid(self) -> bool:
        return not self.inside_other_surface and not self.has_opposite_normal


def bounds_intersect(
    first: Bounds,
    second: Bounds,
    *,
    abs_tol: float = 1e-12,
) -> bool:
    """Return True when two closed cuboids share at least one point."""

    return (
        first.xmax >= second.xmin - abs_tol
        and second.xmax >= first.xmin - abs_tol
        and first.ymax >= second.ymin - abs_tol
        and second.ymax >= first.ymin - abs_tol
        and first.zmax >= second.zmin - abs_tol
        and second.zmax >= first.zmin - abs_tol
    )


def point_in_closed_bounds(
    point: np.ndarray,
    bounds: Bounds,
    *,
    abs_tol: float = 1e-12,
) -> bool:
    """Return True when a point is inside or on a cuboid."""

    x, y, z = np.asarray(point, dtype=float)
    return (
        bounds.xmin - abs_tol <= x <= bounds.xmax + abs_tol
        and bounds.ymin - abs_tol <= y <= bounds.ymax + abs_tol
        and bounds.zmin - abs_tol <= z <= bounds.zmax + abs_tol
    )


def point_strictly_inside_bounds(
    point: np.ndarray,
    bounds: Bounds,
    *,
    abs_tol: float = 1e-12,
) -> bool:
    """Return True only for points in the cuboid interior, not its boundary."""

    x, y, z = np.asarray(point, dtype=float)
    return (
        bounds.xmin + abs_tol < x < bounds.xmax - abs_tol
        and bounds.ymin + abs_tol < y < bounds.ymax - abs_tol
        and bounds.zmin + abs_tol < z < bounds.zmax - abs_tol
    )


def faces_containing_point(
    surface: GaussianSurface,
    point: np.ndarray,
    *,
    abs_tol: float = 1e-12,
) -> tuple[SurfaceFace, ...]:
    """Return all faces of a cuboid BGS containing the point."""

    if not point_in_closed_bounds(point, surface.bounds, abs_tol=abs_tol):
        return ()

    x, y, z = np.asarray(point, dtype=float)
    bounds = surface.bounds

    coordinates_on_face = {
        "NX": math.isclose(x, bounds.xmin, rel_tol=0.0, abs_tol=abs_tol),
        "PX": math.isclose(x, bounds.xmax, rel_tol=0.0, abs_tol=abs_tol),
        "NY": math.isclose(y, bounds.ymin, rel_tol=0.0, abs_tol=abs_tol),
        "PY": math.isclose(y, bounds.ymax, rel_tol=0.0, abs_tol=abs_tol),
        "NZ": math.isclose(z, bounds.zmin, rel_tol=0.0, abs_tol=abs_tol),
        "PZ": math.isclose(z, bounds.zmax, rel_tol=0.0, abs_tol=abs_tol),
    }

    return tuple(
        face
        for face in surface.faces
        if coordinates_on_face[face.direction]
    )


def point_on_surface(
    surface: GaussianSurface,
    point: np.ndarray,
    *,
    abs_tol: float = 1e-12,
) -> bool:
    """Return True when a point lies on at least one face of a cuboid BGS."""

    return bool(faces_containing_point(surface, point, abs_tol=abs_tol))


def normals_are_opposite(
    first: np.ndarray,
    second: np.ndarray,
    *,
    abs_tol: float = 1e-12,
) -> bool:
    """Return True when two unit axis-aligned normals point oppositely."""

    dot_product = float(np.dot(first, second))
    return math.isclose(dot_product, -1.0, rel_tol=0.0, abs_tol=abs_tol)


def build_neighbor_lists(
    surfaces: Sequence[GaussianSurface],
    *,
    abs_tol: float = 1e-12,
) -> tuple[tuple[int, ...], ...]:
    """
    Precompute intersecting BGS indices for Algorithm 4.1 Steps 3 and 4.
    """

    surface_list = list(surfaces)
    neighbors: list[list[int]] = [[] for _ in surface_list]

    for first_index, first in enumerate(surface_list):
        for second_index in range(first_index + 1, len(surface_list)):
            second = surface_list[second_index]
            if bounds_intersect(first.bounds, second.bounds, abs_tol=abs_tol):
                neighbors[first_index].append(second_index)
                neighbors[second_index].append(first_index)

    return tuple(tuple(indices) for indices in neighbors)


def classify_candidate(
    surfaces: Sequence[GaussianSurface],
    source_surface_index: int,
    source_face: SurfaceFace,
    point: np.ndarray,
    *,
    neighbor_indices: Sequence[int] | None = None,
    abs_tol: float = 1e-12,
) -> CandidateClassification:
    """
    Apply the geometric tests in Algorithm 4.1 Steps 3, 4, and 6.

    `coincident_surface_count` counts BGSs whose boundaries contain the point,
    including the source BGS.  A BGS is counted once even at its edge or corner.
    """

    if not 0 <= source_surface_index < len(surfaces):
        raise IndexError("source_surface_index is outside the BGS list.")

    source_surface = surfaces[source_surface_index]
    if not any(face is source_face for face in source_surface.faces):
        raise ValueError("source_face does not belong to source_surface_index.")

    if not point_on_surface(source_surface, point, abs_tol=abs_tol):
        raise ValueError("The proposed point is not on the selected source BGS.")

    #get indexes of surfaces to check for Step 3
    if neighbor_indices is None:
        indices_to_check = (
            index
            for index in range(len(surfaces))
            if index != source_surface_index
        )
    else:
        indices_to_check = (
            index
            for index in neighbor_indices
            if index != source_surface_index
        )

    #step 4
    #nc
    coincident_count = 1

    for other_index in indices_to_check:
        other_surface = surfaces[other_index]

        if point_strictly_inside_bounds( point, other_surface.bounds, abs_tol=abs_tol, ):
            return CandidateClassification(
                inside_other_surface=True,
                has_opposite_normal=False,
                coincident_surface_count=coincident_count,
            )

        other_faces = faces_containing_point( other_surface, point, abs_tol=abs_tol, )
        if not other_faces:
            continue

        if any( 
            normals_are_opposite(
                source_face.normal,
                other_face.normal,
                abs_tol=abs_tol,
            )
            for other_face in other_faces
        ):
            return CandidateClassification(
                inside_other_surface=False,
                has_opposite_normal=True,
                coincident_surface_count=coincident_count + 1,
            )

        coincident_count += 1

    return CandidateClassification(
        inside_other_surface=False,
        has_opposite_normal=False,
        coincident_surface_count=coincident_count,
    )
