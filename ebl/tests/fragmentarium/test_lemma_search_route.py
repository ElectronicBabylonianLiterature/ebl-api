import falcon

from ebl.tests.factories.fragment import LemmatizedFragmentFactory


def test_search_fragment(client, fragmentarium, dictionary, word):
    lemmatized_fragment = LemmatizedFragmentFactory.build()
    matching_word = {**word, "_id": "ginâ I"}
    dictionary.create(word)
    dictionary.create(matching_word)
    fragmentarium.create(lemmatized_fragment)

    result = client.simulate_get(f"/lemmas", params={"word": "GI₆"})

    assert result.status == falcon.HTTP_OK
    assert result.json == [[matching_word]]
    assert result.headers["Access-Control-Allow-Origin"] == "*"


def test_search_fragment_no_query(client):
    result = client.simulate_get(f"/lemmas")

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_search_too_many_params(client):
    params = {"word": "GI₆", "this_param": "is wrong"}
    result = client.simulate_get(f"/lemmas", params=params)

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_search_invalid_param(client):
    params = {"this_param": "is wrong"}
    result = client.simulate_get(f"/lemmas", params=params)

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
