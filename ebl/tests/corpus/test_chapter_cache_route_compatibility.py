import falcon
import attr
import pytest
from falcon import testing

from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.dictionary.domain.word import WordId
from ebl.tests.corpus import test_chapter_cache_races
from ebl.tests.corpus.support import create_chapter_url, simulate_get
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.tokens import ValueToken


cached_chapter = test_chapter_cache_races.cached_chapter


@pytest.mark.parametrize(
    "query", ["lines=0&lines=1&variants=0", "lines=0&variants=0&variants=1"]
)
def test_partial_display_ignores_unpaired_selection_parameters(
    client: testing.TestClient, cached_chapter: Chapter, query: str
) -> None:
    result = simulate_get(
        client, create_chapter_url(cached_chapter, f"/display?{query}")
    )
    assert result.status == falcon.HTTP_OK
    body = result.json
    assert isinstance(body, dict)
    assert len(body["lines"]) == 1
    assert len(body["lines"][0]["variants"]) == 1


def test_sign_routes_keep_their_existing_wire_shape(
    client: testing.TestClient, cached_chapter: Chapter
) -> None:
    result = simulate_get(client, create_chapter_url(cached_chapter, "/signs"))
    assert result.status == falcon.HTTP_OK
    body = result.json
    assert isinstance(body, dict)
    assert set(body) == {"signs", "manuscripts", "textId", "stage", "name"}
    assert body["signs"] == list(cached_chapter.signs)
    all_signs = simulate_get(client, "/corpus/all-signs")
    assert all_signs.status == falcon.HTTP_OK
    assert all_signs.json == [result.json]


@pytest.mark.parametrize("genre", ["", "&genre=Sum"])
def test_lemma_search_with_no_matches_keeps_array_response(
    client: testing.TestClient, genre: str
) -> None:
    result = simulate_get(client, f"/lemmasearch?lemma=absent%20I{genre}")
    assert result.status == falcon.HTTP_OK
    assert result.json == []


def test_corpus_lookup_rejects_invalid_fragment_identity(
    client: testing.TestClient,
) -> None:
    result = simulate_get(client, "/fragments/not-a-museum-number/corpus")
    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_lemma_result_contains_the_existing_display_shape(
    client: testing.TestClient,
    cached_chapter: Chapter,
    text_repository: MongoTextRepository,
) -> None:
    lemma = AkkadianWord.of((ValueToken.of("ina"),), unique_lemma=(WordId("ina I"),))
    variant = attr.evolve(
        cached_chapter.lines[0].variants[0], reconstruction=(lemma,), manuscripts=()
    )
    line = attr.evolve(cached_chapter.lines[0], variants=(variant,))
    text_repository.update(
        cached_chapter.id_, attr.evolve(cached_chapter, lines=(line,))
    )
    result = simulate_get(client, "/lemmasearch?lemma=ina%20I")
    assert result.status == falcon.HTTP_OK
    body = result.json
    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]["lineDetails"] == {"variants": [{"manuscripts": []}]}
