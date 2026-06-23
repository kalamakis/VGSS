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

The current target is correctness for coordinates of roughly `0` to `10`.
Dielectric transitions, non-Manhattan geometry, and FRW hops are not implemented.

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
vgss-sample input/INPUTFILE_TOUCHING_DIRECT.m \
    --net-master C1 \
    --count 10 \
    --seed 1234
```

Save the accepted coordinates as CSV:

```bash
vgss-sample input/INPUTFILE_TOUCHING_DIRECT.m \
    --net-master C1 \
    --count 1000 \
    --seed 1234 \
    --save-points output/vgss_points.csv
```

## Python interface

```python
import numpy as np

from bgs.matlab_parser import parse_matlab_geometry
from bgs.sampling import sample_on_vgss
from bgs.vgss import build_vgss_for_conductor

conductors = parse_matlab_geometry("input/INPUTFILE_TOUCHING_DIRECT.m")
net_vgss = build_vgss_for_conductor(conductors, "C1")

rng = np.random.default_rng(1234)
r = sample_on_vgss(net_vgss.sampling_context, rng)
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

## Tests

```bash
pytest
```
