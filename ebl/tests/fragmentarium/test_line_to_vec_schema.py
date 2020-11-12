from ebl.fragmentarium.application.fragment_schema import LineToVecSchema
from ebl.fragmentarium.domain.fragment import LineToVec


def test_line_to_vec_schema():
    line_to_vec = LineToVec((1, 2, 1, 1, 2))
    assert {"lineToVec": [1, 2, 1, 1, 2], "complexity": 2} == LineToVecSchema().dump(
        line_to_vec
    )
    assert line_to_vec.line_to_vec == (1, 2, 1, 1, 2)
    assert line_to_vec.complexity == 2
