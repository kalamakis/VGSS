import argparse
import sys
from pathlib import Path

import numpy as np

from bgs.matlab_parser import parse_matlab_geometry
from bgs.vgss import build_all_net_vgss
from .random_walk import run_frw_geometry, visualize_3d_walk


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the FRW geometric sampler on a MATLAB-style conductor input file."
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the MATLAB-style geometry input file.",
    )
    parser.add_argument(
        "--scale-factor",
        type=float,
        default=1.25,
        help="Scale factor for VGSS generation. Default: 1.25.",
    )
    parser.add_argument(
        "--max-distance",
        type=float,
        default=10.0,
        help="Maximum distance fallback for VGSS. Default: 10.0.",
    )
    parser.add_argument(
        "--walks",
        type=int,
        default=5000,
        help="Number of random walks to perform. Default: 5000.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1234,
        help="Random seed for reproducibility. Default: 1234.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("../../output") / "frw_exported_data.json",
        help="Path to export the FRW walk data JSON. Default: output/frw_exported_data.json",
    )
    return parser


if __name__ == "__main__":
    args = _build_parser().parse_args()

    filename = args.input_file
    print(f"Reading geometry from {filename}...\n")

    try:
        system_conductors = parse_matlab_geometry(filename)
    except FileNotFoundError:
        print(f"ERROR: Could not find '{filename}'")
        raise SystemExit(1)

    if not system_conductors:
        print("No conductors found in the file.")
        raise SystemExit(1)

    # print("Parsed Conductors:")
    # for conductor in system_conductors:
    #     print(conductor)

    all_net_vgss = build_all_net_vgss(
        system_conductors,
        scale_factor=args.scale_factor,
        max_distance=args.max_distance,
    )
    master_vgss = all_net_vgss[0]
    rng = np.random.default_rng(args.seed)

    visualize_3d_walk(system_conductors, master_vgss, rng)

    print("\nExecuting Batch Geometric Walk Engine...")
    print(f"Master Net: {master_vgss.net.name}")
    print(f"Conductors: {', '.join(master_vgss.net.conductor_names)}")
    print("-" * 30)

    export_data = run_frw_geometry(
        system_conductors,
        master_vgss,
        rng,
        num_walks=args.walks,
    )

    print(f"Total Walks Completed: {len(export_data['walks'])}")
    print(f"Estimated H: {export_data['H']:.6f}")

    output_filename = args.output
    output_filename.parent.mkdir(parents=True, exist_ok=True)
    print(f"\nExporting all walk data to {output_filename}...")

    with open(output_filename, "w") as outfile:
        import json
        json.dump(export_data, outfile, indent=4)

    print(f"Success! Data for {args.walks} walks successfully saved.")
