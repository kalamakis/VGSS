"""
Reserved for the later implementation of Algorithm 4.1: SampleOnVGSS.

The generated GaussianSurface objects already expose:
- total BGS area,
- six rectangular faces,
- each face's area,
- vertices,
- outward normal.

The next milestone can add:
1. area-weighted BGS selection,
2. area-weighted face selection,
3. uniform point sampling on a rectangular face,
4. rejection checks for coincident or enclosed surfaces,
5. the n_c(r) correction,
6. importance sampling using p(r) / U.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from .models import GaussianSurface, SurfaceFace


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


def choose_surface_by_area(
    surfaces: Sequence[GaussianSurface],
    rng: np.random.Generator,
) -> GaussianSurface:
    """Area-weighted BGS choice: the first step of Algorithm 4.1."""

    if not surfaces:
        raise ValueError("At least one Gaussian surface is required.")

    areas = np.asarray([surface.area for surface in surfaces], dtype=float)
    probabilities = areas / areas.sum()
    index = int(rng.choice(len(surfaces), p=probabilities))
    return surfaces[index]


def choose_face_by_area(
    surface: GaussianSurface,
    rng: np.random.Generator,
) -> SurfaceFace:
    """Area-weighted face choice for uniform sampling over one cuboid BGS."""

    areas = np.asarray([face.area for face in surface.faces], dtype=float)
    probabilities = areas / areas.sum()
    index = int(rng.choice(len(surface.faces), p=probabilities))
    return surface.faces[index]


def sample_on_vgss(*args, **kwargs):
    raise NotImplementedError(
        "Full SampleOnVGSS rejection sampling is reserved for the next milestone."
    )
