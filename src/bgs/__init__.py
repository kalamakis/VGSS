"""Boundary Gaussian Surface generation for axis-aligned conductor boxes."""

from .models import Bounds, Conductor, GaussianSurface, SurfaceFace
from .gaussian_surface import (
    BGSGenerationResult,
    UnsupportedGeometryError,
    generate_bgs,
    generate_all_bgs,
)

__all__ = [
    "Bounds",
    "Conductor",
    "GaussianSurface",
    "SurfaceFace",
    "BGSGenerationResult",
    "UnsupportedGeometryError",
    "generate_bgs",
    "generate_all_bgs",
]
