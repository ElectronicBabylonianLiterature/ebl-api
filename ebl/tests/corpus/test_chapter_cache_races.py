import json
from typing import Callable, Sequence, cast

import attr
import falcon
import pytest
from falcon import testing

from ebl.bibliography.application.bibliography import Bibliography
from ebl.corpus.application.corpus import Corpus
from ebl.corpus.domain.chapter import Chapter, ChapterId
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.tests.corpus.support import (
    allow_references,
    allow_signs,
    create_chapter_dto,
    create_chapter_url,
    simulate_get,
)
from ebl.tests.factories.corpus import ChapterFactory, TextFactory
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.sign import Sign
from ebl.transliteration.domain.text_line import TextLine


@pytest.fixture
def cached_chapter(
    text_repository: MongoTextRepository,
    bibliography: Bibliography,
    sign_repository: SignRepository,
    signs: Sequence[Sign],
) -> Chapter:
    chapter = ChapterFactory.build()
    text = TextFactory.build(
        genre=chapter.text_id.genre,
        category=chapter.text_id.category,
        index=chapter.text_id.index,
    )
    allow_signs(signs, sign_repository)
    allow_references(chapter, bibliography)
    text_repository.create(text)
    text_repository.create_chapter(chapter)
    return chapter


def changed_lines_payload(chapter: Chapter) -> dict:
    line = chapter.lines[0]
    variant = line.variants[0]
    manuscript_line = variant.manuscripts[0]
    changed_manuscript_line = attr.evolve(
        manuscript_line,
        line=attr.evolve(
            cast(TextLine, manuscript_line.line), line_number=LineNumber(88, True)
        ),
    )
    changed_variant = attr.evolve(
        variant, manuscripts=(changed_manuscript_line, *variant.manuscripts[1:])
    )
    changed_line = attr.evolve(line, variants=(changed_variant, *line.variants[1:]))
    updated = attr.evolve(chapter, lines=(changed_line, *chapter.lines[1:]))
    return {
        "new": [],
        "deleted": [],
        "edited": [{"index": 0, "line": create_chapter_dto(updated)["lines"][0]}],
    }


@pytest.mark.parametrize(
    "read_method,suffix",
    [
        ("find_chapter_for_display", "/display"),
        ("find_line_with_manuscript_joins", "/lines/0"),
    ],
)
def test_old_read_finishing_after_save_does_not_poison_cache(
    client: testing.TestClient,
    cached_chapter: Chapter,
    monkeypatch: pytest.MonkeyPatch,
    read_method: str,
    suffix: str,
) -> None:
    original: Callable[..., object] = getattr(Corpus, read_method)
    read_count = 0

    def delayed_read(corpus: Corpus, chapter_id: ChapterId, *args: object) -> object:
        nonlocal read_count
        previous = original(corpus, chapter_id, *args)
        read_count += 1
        if read_count == 1:
            saved = client.simulate_post(
                create_chapter_url(cached_chapter, "/lines"),
                body=json.dumps(changed_lines_payload(cached_chapter)),
            )
            assert isinstance(saved, testing.Result)
            assert saved.status == falcon.HTTP_OK
        return previous

    monkeypatch.setattr(Corpus, read_method, delayed_read)
    endpoint = create_chapter_url(cached_chapter, suffix)
    old_response = simulate_get(client, endpoint)
    fresh_response = simulate_get(client, endpoint)
    reused_response = simulate_get(client, endpoint)
    assert old_response.status == fresh_response.status == falcon.HTTP_OK
    assert old_response.json != fresh_response.json
    assert fresh_response.json == reused_response.json
    assert read_count == 2
