import falcon

from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import LemmatizedFragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber


def get_lemmatizable_tokens(fragment):
    for line in fragment.text.text_lines:
        for token in line.content:
            if token.lemmatizable and token.unique_lemma:
                yield token


def test_collect_lemmas(client, fragmentarium, word_repository, word):
    fragment = LemmatizedFragmentFactory.build()
    fragmentarium.create(fragment)

    expected = {}

    for token in get_lemmatizable_tokens(fragment):
        lemmas = []
        for word_id in token.unique_lemma:
            word = {**word, "_id": word_id}
            word_repository.create(word)
            lemmas.append(word)
        expected[token.clean_value] = lemmas

    url = f"/fragments/{fragment.number}/collect-lemmas"
    get_result = client.simulate_get(url)

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == expected


def test_update_lemma_annotation(client, fragmentarium, user):
    fragment = LemmatizedFragmentFactory.build()
    fragmentarium.create(fragment)

    raw_annotation = {"1": {"1": ["foobar I"]}}
    cast_annotation = {1: {1: ["foobar I"]}}

    url = f"/fragments/{fragment.number}/lemma-annotation"
    post_result = client.simulate_post(url, json=raw_annotation)

    updated_fragment = create_response_dto(
        fragment.update_lemma_annotation(cast_annotation),
        user,
        fragment.number == MuseumNumber("K", "1"),
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == updated_fragment
