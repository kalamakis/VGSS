# Boundary Gaussian Surface Generator

This project is a small Python implementation of the conductor-only part of
Algorithm 4.2. Its purpose is to generate a cuboid Boundary Gaussian Surface
around a selected conductor block.

The program reads simple MATLAB-style geometry files, calculates the distances
between the selected conductor and the surrounding conductors, constructs the
Gaussian surface, and displays the result in a 3D plot.

#Algorithm generate_bgs

This code is split in files each for a specific task.
To explain in short what each file does:
1. __init__.py
    -Marks the bgs folder as a python package.
    -Exposes the most useful classes and functions so that they can be 
    imported from other files. 

2. models.py
    -Defines the basic data structures used 
    -Contains classes for:
        *conductor bounding boxes
        *conductor blocks
        *Gaussian surfaces
        *individual faces of a Gaussian surfaces

3. matlab_parser.py
    -Reads the MATLAB-style input file. 
    -Searches for blocks and converts them into python objects

4. Distances.py
    -contains the geometric distance calculations.
    -It calculates the six signed directional distances which is
    the maximum of the six directional distances, according to Definition 4.2.

5. gaussian_surface.py
    -Implements the main Gaussian-surface generation logic.
    -It uses the directional distances to determine how far each
    face of the Boundary Gaussian Surface can move away from the selected conductor.

6. visualization.py
    -Creates the 3D plot.
    It displays:
        *all conductors,
        *the selected master conductor,
        *the generated Gaussian surface around it.

7. main.py
    1. reads the command-line arguments,
    2. loads the input file,
    3. selects the master conductor,
    4. generates the Gaussian surface,
    5. prints the intermediate calculations,
    6. opens or saves the 3D plot.

## Setup

### Linux or macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"

## Run the demo

Generate the BGS for `C1`, use a scale factor of `2`, print the calculations,
and save the plot:

```bash
bgs-generate input/INPUTFILE_05.m --master C1 --scale-factor 2 --save-plot output/C1_bgs.png
```
