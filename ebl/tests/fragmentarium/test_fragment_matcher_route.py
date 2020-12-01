import falcon  # pyre-ignore
import pytest  # pyre-ignore[21]

from ebl.fragmentarium.domain.fragment import LineToVecEncoding
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.tests.factories.fragment import TransliteratedFragmentFactory


@pytest.mark.parametrize("params", ["X.0", "[0,1,1,1,1,1,2]"])
def test_fragment_matcher_route(params, client, fragmentarium, user, database):
    fragment_1 = TransliteratedFragmentFactory.build(number=MuseumNumber.of("X.0"))
    fragment_2 = TransliteratedFragmentFactory.build(
        number=MuseumNumber.of("X.1"),
        line_to_vec=LineToVecEncoding.from_list([1, 1, 2]),
    )
    fragmentarium.create(fragment_1)
    fragmentarium.create(fragment_2)
    get_result = client.simulate_get(f"/fragments/{params}/match")
    assert get_result.status == falcon.HTTP_OK
    assert get_result.headers["Access-Control-Allow-Origin"] == "*"
    assert get_result.json == {
        "score": [["X.0", 7], ["X.1", 3]],
        "scoreWeighted": [["X.0", 6], ["X.1", 3]],
    }
