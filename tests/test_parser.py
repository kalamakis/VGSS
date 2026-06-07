from pathlib import Path

from bgs.matlab_parser import parse_matlab_geometry


def test_uploaded_example_is_parsed() -> None:
    path = Path(__file__).parents[1] / "input" / "INPUTFILE_05.m"
    conductors = parse_matlab_geometry(path)

    assert [item.name for item in conductors] == ["C1", "C2", "C3", "C4", "C5"]

    c1 = conductors[0]
    assert c1.bounds.xmin == 0
    assert c1.bounds.xmax == 1
    assert c1.bounds.ymin == 0
    assert c1.bounds.ymax == 1
    assert c1.bounds.zmin == 0
    assert c1.bounds.zmax == 1
    assert c1.relative_permittivity == 3
