import falcon

from ebl.tests.factories.fragment import TransliteratedFragmentFactory


PATH = "/statistics"


def test_get_statistics(guest_client):
    result = guest_client.simulate_get(PATH)

    assert result.json == {
        "transliteratedFragments": 0,
        "lines": 0,
        "totalFragments": 0,
    }
    assert result.status == falcon.HTTP_OK
    assert result.headers["Cache-Control"] == "public, max-age=600"


def test_get_statistics_cache(cached_client, fragmentarium):
    first_result = cached_client.simulate_get(PATH)
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragmentarium.create(transliterated_fragment)
    second_result = cached_client.simulate_get(PATH)

    assert second_result.json == first_result.json
