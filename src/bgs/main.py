from __future__ import annotations

import argparse
import math
from pathlib import Path

from .gaussian_surface import (
    BGSGenerationResult,
    UnsupportedGeometryError,
    generate_all_bgs,
    generate_bgs,
)
from .matlab_parser import parse_matlab_geometry
from .models import DIRECTIONS
from .visualization import plot_geometry


def _format_value(value: float) -> str:
    return "inf" if math.isinf(value) else f"{value:.6g}"


def _print_result(result: BGSGenerationResult) -> None:
    print()
    print("=" * 78)
    print(f"Master conductor: {result.master.name}")
    print("=" * 78)

    header = (
        f"{'Other':<10}"
        + "".join(f"{direction:>10}" for direction in DIRECTIONS)
        + f"{'d(A,B)':>10}"
        + f"{'limits':>16}"
    )
    print(header)
    print("-" * len(header))

    for row in result.pairwise_rows:
        values = "".join(
            f"{_format_value(row.signed_distances[direction]):>10}"
            for direction in DIRECTIONS
        )
        limits = ",".join(row.limiting_directions)
        print(
            f"{row.other_conductor:<10}"
            f"{values}"
            f"{_format_value(row.overall_distance):>10}"
            f"{limits:>16}"
        )

    print()
    print("Initial extents from conductor distances:")
    for direction in DIRECTIONS:
        print(f"  D[{direction}] = {_format_value(result.initial_extents[direction])}")

    print()
    if result.used_isolated_fallback:
        print("No finite conductor constraint was found.")
        print(f"Applied isolated-conductor fallback: {result.cap_distance:.6g}")
    else:
        print(
            "Scale-factor cap: "
            f"min(finite initial extents) * scale_factor = {result.cap_distance:.6g}"
        )

    print("Final extents:")
    for direction in DIRECTIONS:
        print(f"  D[{direction}] = {_format_value(result.final_extents[direction])}")

    bounds = result.gaussian_surface.bounds
    print()
    print("Generated BGS bounds:")
    print(f"  x: [{bounds.xmin:.6g}, {bounds.xmax:.6g}]")
    print(f"  y: [{bounds.ymin:.6g}, {bounds.ymax:.6g}]")
    print(f"  z: [{bounds.zmin:.6g}, {bounds.zmax:.6g}]")
    print(f"  total surface area: {result.gaussian_surface.area:.6g}")

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a Gaussian surface around one conductor."
    )

    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the MATLAB-style geometry file.",
    )

    parser.add_argument(
        "--master",
        default="C1",
        help="Conductor around which the BGS is generated. Default: C1.",
    )

    parser.add_argument(
        "--scale-factor",
        type=float,
        default=1.0,
        help="Algorithm 4.2 scale factor. Default: 1.",
    )

    parser.add_argument(
        "--save-plot",
        type=Path,
        default=None,
        help="Optional path for saving the 3D plot.",
    )

    return parser
def main() -> None:
    args = _build_parser().parse_args()

    conductors = parse_matlab_geometry(args.input_file)

    master = next(
        conductor
        for conductor in conductors
        if conductor.name == args.master
    )

    result = generate_bgs(
        master,
        conductors,
        scale_factor=args.scale_factor,
    )

    if result is None:
        raise SystemExit("The BGS could not be generated.")

    _print_result(result)

    plot_geometry(
        conductors,
        selected_surface=result.gaussian_surface,
        save_path=args.save_plot,
        show=True,
    )


if __name__ == "__main__":
    try:
        main()
    except UnsupportedGeometryError as exc:
        raise SystemExit(str(exc)) from exc
