import falcon
import pytest

from ebl.tests.factories.fragment import LemmatizedFragmentFactory


@pytest.mark.parametrize(
    "query_word,lemma,is_normalized",
    [("GI₆", "ginâ I", False), ("kur", "normalized I", True)],
)
def test_search_fragment(
    query_word, lemma, is_normalized, client, fragmentarium, dictionary, word
):
    expected_word = {**word, "_id": lemma}
    lemmatized_fragment = LemmatizedFragmentFactory.build()
    fragmentarium.create(lemmatized_fragment)
    dictionary.create(expected_word)
    result = client.simulate_get(
        "/lemmas", params={"word": query_word, "isNormalized": is_normalized}
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == [[expected_word]]


def test_search_fragment_no_query(client):
    result = client.simulate_get("/lemmas")

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize(
    "params",
    [
        {"word": "GI₆", "this_param": "is wrong"},
        {"this_param": "is wrong"},
        {"word": "GI₆", "isNormalized": "invalid"},
        {"isNormalized": "true"},
    ],
)
def test_search_invalid_params(client, params):
    result = client.simulate_get("/lemmas", params=params)

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
