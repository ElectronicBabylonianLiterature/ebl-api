from itertools import chain
from typing import Any, Dict, Iterable, cast

import pytest
from falcon import testing

from ebl.bibliography.application.bibliography import Bibliography
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.web.chapter_schemas import ApiChapterSchema
from ebl.corpus.web.display_schemas import LineDetailsDisplay, LineDetailsDisplaySchema
from ebl.tests.factories.corpus import ChapterFactory
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.sign import Sign
from ebl.users.domain.user import Guest


ANY_USER = Guest()


def allow_references(chapter: Chapter, bibliography: Bibliography) -> None:
    for manuscript in chapter.manuscripts:
        for reference in chain(
            manuscript.references,
            (old_siglum.reference for old_siglum in manuscript.old_sigla),
        ):
            document = reference.document
            assert document is not None
            bibliography.create(document, ANY_USER)


def allow_signs(signs: Iterable[Sign], sign_list: SignRepository) -> None:
    for sign in signs:
        sign_list.create(sign)


def store_chapter(request: pytest.FixtureRequest) -> Chapter:
    allow_signs(
        request.getfixturevalue("signs"), request.getfixturevalue("sign_repository")
    )
    chapter = ChapterFactory.build()
    allow_references(chapter, request.getfixturevalue("bibliography"))
    request.getfixturevalue("text_repository").create_chapter(chapter)
    return chapter


def create_chapter_dto(chapter: Chapter) -> dict:
    return cast(dict, ApiChapterSchema().dump(chapter))


def simulate_get(client: testing.TestClient, url: str) -> testing.Result:
    result = client.simulate_get(url)
    assert isinstance(result, testing.Result)
    return result


def create_chapter_url(chapter: Chapter, suffix: str = "") -> str:
    return (
        f"/texts/{chapter.text_id.genre.value}"
        f"/{chapter.text_id.category}/{chapter.text_id.index}"
        f"/chapters/{chapter.stage.long_name}/{chapter.name}{suffix}"
    )


def dump_line_details(chapter: Chapter, index: int) -> Dict[str, Any]:
    return cast(
        Dict[str, Any],
        LineDetailsDisplaySchema().dump(
            LineDetailsDisplay.from_line_manuscripts(
                chapter.lines[index], chapter.manuscripts
            )
        ),
    )


def get_line(
    client: testing.TestClient, chapter: Chapter, number: object
) -> testing.Result:
    return simulate_get(client, create_chapter_url(chapter, f"/lines/{number}"))
