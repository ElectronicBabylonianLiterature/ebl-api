import falcon
import attr
import pytest
from dataclasses import dataclass
from falcon import testing

from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.dictionary.domain.word import WordId
from ebl.tests.corpus import test_chapter_cache_races
from ebl.tests.corpus.support import create_chapter_url, simulate_get
from ebl.tests.factories.corpus import LineFactory, LineVariantFactory
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.tokens import ValueToken


cached_chapter = test_chapter_cache_races.cached_chapter


@dataclass(frozen=True)
class SelectionCase:
    query: str
    line_index: int
    variant_index: int
    unpaired_line_index: int | None = None


@pytest.mark.parametrize(
    "selection",
    [
        SelectionCase("lines=0&lines=1&variants=0", 0, 0, 1),
        SelectionCase("lines=1&variants=1&variants=0", 1, 1),
    ],
)
def test_partial_display_preserves_selection_content(
    client: testing.TestClient,
    cached_chapter: Chapter,
    text_repository: MongoTextRepository,
    selection: SelectionCase,
) -> None:
    lines = [
        LineFactory.build(
            manuscript_id=1,
            variants=LineVariantFactory.build_batch(2, manuscript_id=1),
        )
        for _ in range(2)
    ]
    text_repository.update(cached_chapter.id_, attr.evolve(cached_chapter, lines=lines))
    full_result = simulate_get(client, create_chapter_url(cached_chapter, "/display"))
    full_body = full_result.json
    assert isinstance(full_body, dict)
    assert full_body["lines"][0] != full_body["lines"][1]
    assert full_body["lines"][0]["variants"][0] != full_body["lines"][0]["variants"][1]
    result = simulate_get(
        client, create_chapter_url(cached_chapter, f"/display?{selection.query}")
    )
    assert result.status == falcon.HTTP_OK
    body = result.json
    assert isinstance(body, dict)
    expected_line = full_body["lines"][selection.line_index]
    expected_lines = [
        {
            **expected_line,
            "variants": [expected_line["variants"][selection.variant_index]],
        }
    ]
    if selection.unpaired_line_index is not None:
        unpaired_line = full_body["lines"][selection.unpaired_line_index]
        expected_lines.append({**unpaired_line, "variants": []})
    assert body["lines"] == expected_lines


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
