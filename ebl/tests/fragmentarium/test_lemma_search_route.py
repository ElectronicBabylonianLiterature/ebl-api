import falcon  # pyre-ignore[21]
import pytest  # pyre-ignore[21]

from ebl.tests.factories.fragment import LemmatizedFragmentFactory


@pytest.mark.parametrize(
    "query_word,lemma,is_normalized",
    [("GI₆", "ginâ I", False), ("kur", "normalized I", True)],
)
def test_search_fragment(
    query_word, lemma, is_normalized, client, fragmentarium, dictionary, word
):
    lemmatized_fragment = LemmatizedFragmentFactory.build()
    matching_word = {**word, "_id": lemma}
    dictionary.create(word)
    dictionary.create(matching_word)
    fragmentarium.create(lemmatized_fragment)

    result = client.simulate_get(
        "/lemmas", params={"word": query_word, "isNormalized": is_normalized}
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == [[matching_word]]
    assert result.headers["Access-Control-Allow-Origin"] == "*"


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
