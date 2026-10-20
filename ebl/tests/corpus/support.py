from itertools import chain
from typing import Iterable, cast

from falcon import testing

from ebl.bibliography.application.bibliography import Bibliography
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.web.chapter_schemas import ApiChapterSchema
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
