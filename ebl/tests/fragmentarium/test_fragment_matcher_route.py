import falcon
from ebl.fragmentarium.domain.line_to_vec_encoding import LineToVecEncoding
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.fragmentarium.application.fragment_schema import ScriptSchema


def test_fragment_matcher_route(client, fragmentarium, user):
    fragment_id = "X.15"

    fragment_1 = TransliteratedFragmentFactory.build(number=MuseumNumber.of("X.15"))
    fragment_2 = TransliteratedFragmentFactory.build(
        number=MuseumNumber.of("X.326"),
        line_to_vec=(LineToVecEncoding.from_list([1, 1, 2]),),
    )
    expected_score = {
        "score": [
            {
                "museumNumber": "X.326",
                "script": ScriptSchema().dump(fragment_2.script),
                "score": 3,
            }
        ],
        "scoreWeighted": [
            {
                "museumNumber": "X.326",
                "script": ScriptSchema().dump(fragment_2.script),
                "score": 5,
            }
        ],
    }
    fragmentarium.create(fragment_1)
    fragmentarium.create(fragment_2)
    get_result = client.simulate_get(f"/fragments/{fragment_id}/match")
    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == expected_score


def test_fragment_matcher_route_error(client, fragmentarium, user):
    faulty_fragment_id = "X.-1"
    fragment_1 = TransliteratedFragmentFactory.build(number=MuseumNumber.of("X.0"))
    fragment_2 = TransliteratedFragmentFactory.build(
        number=MuseumNumber.of("X.1"),
        line_to_vec=(LineToVecEncoding.from_list([1, 1, 2]),),
    )
    fragmentarium.create(fragment_1)
    fragmentarium.create(fragment_2)
    get_result = client.simulate_get(f"/fragments/{faulty_fragment_id}/match")
    assert get_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
