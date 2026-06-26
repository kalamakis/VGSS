# BGS and VGSS sampler

This project implements the conductor-only part of Algorithm 4.2 and the first
correctness-focused version of Algorithm 4.1 (`SampleOnVGSS`) for axis-aligned
cuboid conductor blocks.

It reads MATLAB-style geometry files containing matrices such as:

```matlab
C1 = [
    ...
];
```

Each row represents one rectangular face using four 3D vertices.

## Current scope

- Parse axis-aligned conductor blocks from `.m` files.
- Generate one cuboid Boundary Gaussian Surface (BGS) per block with Algorithm
  4.2.
- Detect electrical nets as connected components of touching blocks.
- Treat face, edge, and corner contact as touching.
- Reject overlapping conductor volumes as invalid input.
- Build one independent VGSS sampling context for each detected net.
- Implement Algorithm 4.1:
  - area-weighted BGS selection;
  - uniform sampling on the selected BGS;
  - rejection of points inside another BGS;
  - rejection of opposite-normal internal interfaces;
  - the `1 / n_c(r)` multiplicity correction;
  - configurable importance rejection `p(r) / U`.
- Use `p(r) = 1` and `U = 1` by default.
- Return only the accepted coordinate `r = [x, y, z]`.
- Visualize conductor blocks, per-net BGSs, and accepted VGSS points in 3D.

The current target is correctness for coordinates of roughly `0` to `10`.
Dielectric transitions and non-Manhattan geometry are not implemented. The existing geometric FRW is connected to the VGSS sampler without replacing its maximal-cube walk logic.

## Setup

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

### Linux or macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Generate BGSs with Algorithm 4.2

One selected conductor:

```bash
bgs-generate input/INPUTFILE_05.m --master C1 --scale-factor 2
```

Every conductor in one combined plot:

```bash
bgs-generate input/INPUTFILE_05.m --all --scale-factor 2 --no-show
```

`--max-distance` is only the fallback extent for a block with no finite
non-touching conductor constraint.

## Sample one net with Algorithm 4.1

`--net-master` identifies the desired net. Every conductor connected to that
block through face, edge, or corner contact belongs to the same net.

```bash
vgss-sample input/INPUTFILE_TOUCHING_DIRECT.m --net-master C1 --count 10 --seed 1234
```

Save the accepted coordinates and a 3D visualization:

```bash
vgss-sample input/INPUTFILE_TOUCHING_DIRECT.m \
    --net-master C1 \
    --count 1000 \
    --seed 1234 \
    --save-points output/vgss_points.csv \
    --save-plot output/net1_vgss.png \
    --no-show
```

## DEMO for vgss
Build and sample every detected net with `build_all_net_vgss()`:

```bash
vgss-sample input/INPUTFILE_TOUCHING_DIRECT.m --all-nets --count 1000 --seed 1234 --save-points output/all_net_vgss_points.csv --save-plot output/all_net_vgss_samples.png
```

With `--all-nets`, `--count` is the number of accepted samples generated for
each net. The CSV contains the columns `net,x,y,z`. The plot uses one color per
net for both its individual BGSs and its accepted points.

## Python interface

```python
import numpy as np

from bgs.matlab_parser import parse_matlab_geometry
from bgs.sampling import sample_on_vgss
from bgs.vgss import build_all_net_vgss, build_vgss_for_conductor
from bgs.visualization import plot_vgss_results

conductors = parse_matlab_geometry("input/INPUTFILE_TOUCHING_DIRECT.m")
net_vgss = build_vgss_for_conductor(conductors, "C1")

rng = np.random.default_rng(1234)
r = sample_on_vgss(net_vgss.sampling_context, rng)

# Build and sample every net.
all_net_vgss = build_all_net_vgss(conductors)
sampled_points = {
    item.net.name: np.vstack(
        [sample_on_vgss(item.sampling_context, rng) for _ in range(200)]
    )
    for item in all_net_vgss
}

plot_vgss_results(
    conductors,
    all_net_vgss,
    sampled_points,
    save_path="output/all_net_vgss_samples.png",
    show=False,
)
```

To replace the default `p(r) = 1`, pass a callable and a valid upper bound while
building the context:

```python
net_vgss = build_vgss_for_conductor(
    conductors,
    "C1",
    importance_function=lambda r: 0.5,
    upper_bound=1.0,
)
```

The sampler raises an error if an evaluated `p(r)` is negative, non-finite, or
larger than `U`.



## FRW usage

The FRW keeps its original maximal-cube walk. The only change to its starting
step is that every walk receives a fresh accepted point from Algorithm 4.1.

```python
import numpy as np

from FRW.random_walk import run_frw_geometry
from bgs.matlab_parser import parse_matlab_geometry
from bgs.vgss import build_all_net_vgss


def F(r: np.ndarray) -> float:
    # Replace this with the book's F(r).
    return 1.0


conductors = parse_matlab_geometry("input/INPUTFILE_TOUCHING_DIRECT.m")

all_net_vgss = build_all_net_vgss(
    conductors,
    scale_factor=1.25,
    max_distance=10.0,
    importance_function=F,
    upper_bound=1.0,  # Must satisfy F(r) <= U over the complete VGSS.
)

rng = np.random.default_rng(1234)

for master_vgss in all_net_vgss:
    result = run_frw_geometry(
        conductors,
        master_vgss,
        rng,
        num_walks=5000,
        max_hops=100,
    )

    print(master_vgss.net.name, result["H"])
```

`result["walks"]` preserves the original walk output (`path_data` and
`hit_conductor`) and additionally stores each accepted `start_point`.
`result["sampling_stats"]` contains the proposal/rejection counts used for:

```text
H = U * total_component_area * accepted_count / proposal_count
```

`H` is a Monte Carlo estimate. More accepted FRW starting points generally make
that estimate more stable.

The original-style executable path uses the first detected net:

```bash
python -m FRW.random_walk input/INPUTFILE_TOUCHING_DIRECT.m
```

## Tests
To run prebuilt tests:
```bash
pytest
```
