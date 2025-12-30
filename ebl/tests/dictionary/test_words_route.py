import json

import falcon
import pytest


@pytest.fixture
def saved_word(dictionary, word):
    word = {**word}
    dictionary.create(word)
    return word


@pytest.fixture
def another_saved_word(dictionary, word):
    word = {**word, "_id": "part1 part2 II"}
    dictionary.create(word)
    return word


def test_get_word(client, saved_word):
    unique_lemma = saved_word["_id"]
    result = client.simulate_get(f"/words/{unique_lemma}")

    assert result.json == saved_word
    assert result.status == falcon.HTTP_OK


def test_get_words(client, saved_word, another_saved_word):
    ids = ",".join([saved_word["_id"], another_saved_word["_id"]])
    result = client.simulate_get("/words", params={"lemmas": ids})

    assert result.json == [saved_word, another_saved_word]
    assert result.status == falcon.HTTP_OK


def test_word_not_found(client):
    result = client.simulate_get("/words/not found")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_search_word(client, saved_word):
    lemma = " ".join(saved_word["lemma"])
    result = client.simulate_get("/words", params={"query": lemma})

    assert result.json == [saved_word]
    assert result.status == falcon.HTTP_OK


def test_search_word_lemma(client, saved_word):
    lemma = saved_word["lemma"][0][:2]
    result = client.simulate_get("/words", params={"lemma": lemma})

    assert result.status == falcon.HTTP_OK
    assert result.json == [saved_word]


def test_search_word_lemma_with_origin(client, saved_word):
    lemma = saved_word["lemma"][0][:2]
    result = client.simulate_get("/words", params={"lemma": lemma, "origin": "CDA"})

    assert result.status == falcon.HTTP_OK
    assert result.json == [saved_word]


def test_search_word_no_query(client):
    result = client.simulate_get("/words")

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_search_word_invalid_query(client):
    result = client.simulate_get("/words", params={"invalid": "lemma"})

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_search_word_double_query(client):
    result = client.simulate_get("/words", params={"query": "lemma", "lemma": "lemma"})

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_search_word_origin_only_is_invalid(client):
    result = client.simulate_get("/words", params={"origin": "CDA"})

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_search_word_with_origin_filter(client, saved_word, dictionary):
    another_word = {**saved_word, "_id": "part1 part2 II", "origin": "EBL"}
    dictionary.create(another_word)

    result = client.simulate_get("/words", params={"query": "part", "origin": "CDA"})

    assert result.json == [saved_word]
    assert result.status == falcon.HTTP_OK


def test_search_word_with_different_origin(client, saved_word, dictionary):
    another_word = {**saved_word, "_id": "part1 part2 II", "origin": "EBL"}
    dictionary.create(another_word)

    result = client.simulate_get("/words", params={"query": "part", "origin": "EBL"})

    assert result.json == [another_word]
    assert result.status == falcon.HTTP_OK


@pytest.mark.parametrize(
    "transform", [lambda word: word, lambda word: {**word, "derived": []}]
)
def test_update_word(transform, client, saved_word, user, database):
    unique_lemma = saved_word["_id"]
    updated_word = transform(saved_word)
    body = json.dumps(updated_word)
    post_result = client.simulate_post(f"/words/{unique_lemma}", body=body)

    assert post_result.status == falcon.HTTP_NO_CONTENT

    get_result = client.simulate_get(f"/words/{unique_lemma}")

    assert get_result.json == updated_word
    assert database["changelog"].find_one(
        {
            "resource_id": unique_lemma,
            "resource_type": "words",
            "user_profile.name": user.profile["name"],
        }
    )


def test_update_word_not_found(client, word):
    unique_lemma = "not found"
    not_found_word = {**word, "_id": unique_lemma}
    body = json.dumps(not_found_word)

    post_result = client.simulate_post(f"/words/{unique_lemma}", body=body)

    assert post_result.status == falcon.HTTP_NOT_FOUND


@pytest.mark.parametrize(
    "transform",
    [lambda word: {**word, "lemma": []}, lambda word: {**word, "derived": [[]]}],
)
def test_update_word_invalid_entity(transform, client, saved_word):
    unique_lemma = saved_word["_id"]
    invalid_word = transform(saved_word)
    body = json.dumps(invalid_word)

    post_result = client.simulate_post(f"/words/{unique_lemma}", body=body)

    assert post_result.status == falcon.HTTP_BAD_REQUEST


def test_list_all_words_route(client, dictionary, word) -> None:
    dictionary.create(word)
    result = client.simulate_get("/words/all")

    assert result.status == falcon.HTTP_OK
    assert result.json == [word["_id"]]
