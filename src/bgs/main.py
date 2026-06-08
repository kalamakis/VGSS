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
        description="Generate Boundary Gaussian Surfaces for conductor blocks."
    )

    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the MATLAB-style geometry input file.",
    )

    # Choose either one conductor or every conductor.
    selection = parser.add_mutually_exclusive_group()

    selection.add_argument(
        "--master",
        default=None,
        help="Generate a BGS around one conductor, for example C1.",
    )

    selection.add_argument(
        "--all",
        action="store_true",
        help="Generate a BGS around every conductor.",
    )

    parser.add_argument(
        "--scale-factor",
        type=float,
        default=1.0,
        help="Scale factor used by Algorithm 4.2. Default: 1.",
    )

    parser.add_argument(
        "--max-distance",
        type=float,
        default=10.0,
        help=(
            "Fallback BGS extent for an isolated conductor. "
            "Default: 10."
        ),
    )

    parser.add_argument(
        "--touch-policy",
        choices=("skip", "error"),
        default="skip",
        help=(
            "What to do when conductors touch or overlap. "
            "Default: skip."
        ),
    )

    parser.add_argument(
        "--save-plot",
        type=Path,
        default=None,
        help="Optional path for saving the generated 3D plot.",
    )

    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Do not open the interactive plot window.",
    )

    return parser

def main() -> None:
    args = _build_parser().parse_args()

    conductors = parse_matlab_geometry(args.input_file)

    print("Loaded conductors:")
    for conductor in conductors:
        print(f"  {conductor.name}")

    # ---------------------------------------------------------
    # MODE 1: Generate one BGS for every conductor
    # ---------------------------------------------------------
    if args.all:
        results = generate_all_bgs(
            conductors,
            scale_factor=args.scale_factor,
            max_distance=args.max_distance,
            touch_policy=args.touch_policy,
        )

        if not results:
            raise SystemExit("No BGS could be generated.")

        for result in results:
            _print_result(result)

        # Draw every generated BGS in one combined figure.
        plot_geometry(
            conductors,
            selected_surfaces=[
                result.gaussian_surface
                for result in results
            ],
            save_path=args.save_plot or Path("output") / "all_bgs.png",
            show=not args.no_show,
        )

        return

    # ---------------------------------------------------------
    # MODE 2: Generate a BGS for only one selected conductor
    # ---------------------------------------------------------
    master = next(
        (
            conductor
            for conductor in conductors
            if conductor.name == args.master
        ),
        None,
    )

    if master is None:
        available = ", ".join(
            conductor.name for conductor in conductors
        )

        raise SystemExit(
            f"Unknown conductor {args.master!r}. "
            f"Available conductors: {available}"
        )

    result = generate_bgs(
        master,
        conductors,
        scale_factor=args.scale_factor,
        max_distance=args.max_distance,
        touch_policy=args.touch_policy,
    )

    if result is None:
        raise SystemExit("The selected BGS was skipped.")

    _print_result(result)

    plot_geometry(
        conductors,
        selected_surface=result.gaussian_surface,
        save_path=args.save_plot,
        show=not args.no_show,
    )


if __name__ == "__main__":
    try:
        main()
    except UnsupportedGeometryError as exc:
        raise SystemExit(str(exc)) from exc
