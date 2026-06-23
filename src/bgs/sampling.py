from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
import math

import numpy as np

from .models import GaussianSurface, SurfaceFace
from .vgss_geometry import build_neighbor_lists, classify_candidate

ImportanceFunction = Callable[[np.ndarray], float]


def uniform_importance(_point: np.ndarray) -> float:
    """Default Algorithm 4.1 importance function: p(r) = 1."""

    return 1.0


def sample_point_uniformly_on_face(
    face: SurfaceFace,
    rng: np.random.Generator,
) -> np.ndarray:
    """Uniformly sample a point on a rectangular face."""

    origin = face.vertices[0]
    edge_1 = face.vertices[1] - origin
    edge_2 = face.vertices[3] - origin
    u, v = rng.random(2)
    return origin + u * edge_1 + v * edge_2


def _normalized_area_probabilities(areas: np.ndarray) -> np.ndarray:
    if areas.ndim != 1 or len(areas) == 0:
        raise ValueError("At least one positive area is required.")
    if not np.all(np.isfinite(areas)) or np.any(areas <= 0.0):
        raise ValueError("All surface areas must be finite and positive.")

    total_area = float(areas.sum())
    if not math.isfinite(total_area) or total_area <= 0.0:
        raise ValueError("The total surface area must be finite and positive.")

    return areas / total_area


def choose_surface_index_by_area(
    surfaces: Sequence[GaussianSurface],
    rng: np.random.Generator,
) -> int:
    """Return an area-weighted BGS index for Algorithm 4.1 Step 1."""

    if not surfaces:
        raise ValueError("At least one Gaussian surface is required.")

    areas = np.asarray([surface.area for surface in surfaces], dtype=float)
    probabilities = _normalized_area_probabilities(areas)
    return int(rng.choice(len(surfaces), p=probabilities))


def choose_surface_by_area(
    surfaces: Sequence[GaussianSurface],
    rng: np.random.Generator,
) -> GaussianSurface:
    """Area-weighted BGS choice: Algorithm 4.1 Step 1."""

    return surfaces[choose_surface_index_by_area(surfaces, rng)]


def choose_face_index_by_area(
    surface: GaussianSurface,
    rng: np.random.Generator,
) -> int:
    """Return an area-weighted face index for uniform BGS sampling."""

    areas = np.asarray([face.area for face in surface.faces], dtype=float)
    probabilities = _normalized_area_probabilities(areas)
    return int(rng.choice(len(surface.faces), p=probabilities))


def choose_face_by_area(
    surface: GaussianSurface,
    rng: np.random.Generator,
) -> SurfaceFace:
    """Area-weighted face choice for uniform sampling over one cuboid BGS."""

    return surface.faces[choose_face_index_by_area(surface, rng)]


@dataclass(frozen=True)
class VGSSSamplingContext:
    """Precomputed data reused by repeated SampleOnVGSS calls for one net."""

    surfaces: tuple[GaussianSurface, ...]
    neighbor_lists: tuple[tuple[int, ...], ...]
    importance_function: ImportanceFunction
    upper_bound: float
    abs_tol: float


def prepare_vgss_sampling(
    surfaces: Sequence[GaussianSurface],
    *,
    importance_function: ImportanceFunction = uniform_importance,
    upper_bound: float = 1.0,
    abs_tol: float = 1e-12,
) -> VGSSSamplingContext:
    """Validate and precompute one net's VGSS sampling context."""

    surface_tuple = tuple(surfaces)
    if not surface_tuple:
        raise ValueError("At least one Gaussian surface is required.")
    if upper_bound <= 0.0 or not math.isfinite(upper_bound):
        raise ValueError("U must be finite and positive.")
    if abs_tol < 0.0 or not math.isfinite(abs_tol):
        raise ValueError("abs_tol must be finite and non-negative.")
    if not callable(importance_function):
        raise TypeError("importance_function must be callable.")

    # Validate areas now instead of failing during a later random draw.
    _normalized_area_probabilities(
        np.asarray([surface.area for surface in surface_tuple], dtype=float)
    )
    for surface in surface_tuple:
        _normalized_area_probabilities(
            np.asarray([face.area for face in surface.faces], dtype=float)
        )

    return VGSSSamplingContext(
        surfaces=surface_tuple,
        neighbor_lists=build_neighbor_lists(surface_tuple, abs_tol=abs_tol),
        importance_function=importance_function,
        upper_bound=float(upper_bound),
        abs_tol=float(abs_tol),
    )


def sample_on_vgss(
    context: VGSSSamplingContext,
    rng: np.random.Generator,
    *,
    max_attempts: int = 10_000,
) -> np.ndarray:
    """
    Implement Algorithm 4.1 and return only the accepted point r.

    The default context uses p(r) = 1 and U = 1.  A different non-negative
    importance function can be supplied when the context is prepared.
    """

    if max_attempts <= 0:
        raise ValueError("max_attempts must be positive.")

    surfaces = context.surfaces

    for _attempt in range(1, max_attempts + 1):
        # Steps 1 and 2: area-weighted BGS selection and uniform point proposal.
        source_surface_index = choose_surface_index_by_area(surfaces, rng)
        source_surface = surfaces[source_surface_index]
        source_face = choose_face_by_area(source_surface, rng)
        point = sample_point_uniformly_on_face(source_face, rng)

        # Steps 3 and 4: reject buried surfaces and opposite-normal interfaces.
        classification = classify_candidate(
            surfaces,
            source_surface_index,
            source_face,
            point,
            neighbor_indices=context.neighbor_lists[source_surface_index],
            abs_tol=context.abs_tol,
        )
        if not classification.is_geometrically_valid:
            continue

        # Step 5: the book draws both independent uniform values together.
        x1, x2 = rng.random(2)

        # Step 6: correct for a point proposed by multiple coincident BGSs.
        multiplicity_acceptance = 1.0 / classification.coincident_surface_count
        if x1 > multiplicity_acceptance:
            continue

        # Step 7: optional importance-sampling rejection p(r) / U.
        importance_value = float(context.importance_function(point))
        if not math.isfinite(importance_value) or importance_value < 0.0:
            raise ValueError("p(r) must be finite and non-negative.")
        if importance_value > context.upper_bound + context.abs_tol:
            raise ValueError(
                f"p(r)={importance_value:.6g} exceeds U={context.upper_bound:.6g}."
            )

        importance_acceptance = min(
            1.0,
            importance_value / context.upper_bound,
        )
        if x2 > importance_acceptance:
            continue

        # Step 8.
        return point

    raise RuntimeError(
        "SampleOnVGSS did not accept a point within "
        f"{max_attempts} attempts. Check the BGS geometry, p(r), and U."
    )
