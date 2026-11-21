import json
from typing import Any, Callable, Dict, Optional, Sequence

import attr
from falcon import testing

from ebl.corpus.application.chapter_edit_writer import ChapterEditWriter, SavedChapter
from ebl.corpus.application.corpus import Corpus
from ebl.corpus.domain.chapter import Chapter, ChapterId
from ebl.corpus.domain.manuscripts_update import ManuscriptsUpdate
from ebl.tests.corpus.outline_support import dump_outline
from ebl.tests.corpus.support import create_chapter_dto, create_chapter_url
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.users.domain.user import User

Outline = Dict[str, Any]
IMPORT_SUFFIX = "/import"
MANUSCRIPTS_SUFFIX = "/manuscripts"
FIRST_IMPORTED_LINE_NUMBER = 10
INVALID_ATF = "invalid atf"


@attr.s(frozen=True, auto_attribs=True)
class ChapterEditRequest:
    suffix: str
    body: str


@attr.s(frozen=True, auto_attribs=True)
class ChapterEdit(ChapterEditRequest):
    save: Callable[[ChapterEditWriter, ChapterId, Optional[str], User], SavedChapter]
    save_with_corpus: Callable[[Corpus, ChapterId, User], Chapter]
    update_outline: Callable[[Outline], Outline]


@attr.s(frozen=True, auto_attribs=True)
class ChapterEditKind:
    suffix: str
    create_edit: Callable[[Chapter, int], ChapterEdit]
    create_invalid_edit: Callable[[Chapter], ChapterEdit]


def _keep_outline(outline: Outline) -> Outline:
    return outline


def _create_import_edit(
    atf: str, update_outline: Callable[[Outline], Outline]
) -> ChapterEdit:
    return ChapterEdit(
        IMPORT_SUFFIX,
        json.dumps({"atf": atf}),
        lambda writer, id_, revision, user: writer.save_imported_lines(
            id_, atf, revision, user
        ),
        lambda corpus, id_, user: corpus.import_lines(id_, atf, user),
        update_outline,
    )


def create_import_edit(chapter: Chapter, step: int) -> ChapterEdit:
    number = FIRST_IMPORTED_LINE_NUMBER + step
    manuscript = chapter.manuscripts[0]

    def append_imported_line(outline: Outline) -> Outline:
        imported_line = {
            "index": len(outline["lines"]),
            "number": str(number),
            "isSecondLineOfParallelism": False,
            "isBeginningOfSection": False,
            "translation": "",
            "variants": [{"reconstruction": "bu", "manuscriptIds": [manuscript.id]}],
        }
        return {**outline, "lines": [*outline["lines"], imported_line]}

    return _create_import_edit(
        f"{number}. bu\n{manuscript.siglum} {step + 1}. ku", append_imported_line
    )


def create_invalid_import_edit(chapter: Chapter) -> ChapterEdit:
    return _create_import_edit(INVALID_ATF, _keep_outline)


def create_manuscripts_update(chapter: Chapter, step: int) -> ManuscriptsUpdate:
    edited_manuscript = attr.evolve(
        chapter.manuscripts[0],
        museum_number=MuseumNumber.of(f"X.{step + 1}"),
        accession="",
    )
    return ManuscriptsUpdate(
        (edited_manuscript, *chapter.manuscripts[1:]),
        (MuseumNumber.of(f"K.{step + 100}"),),
    )


def create_manuscripts_body(chapter: Chapter, update: ManuscriptsUpdate) -> str:
    dto = create_chapter_dto(apply_manuscripts_update(chapter, update))
    return json.dumps(
        {
            "manuscripts": dto["manuscripts"],
            "uncertainFragments": dto["uncertainFragments"],
        }
    )


def apply_manuscripts_update(chapter: Chapter, update: ManuscriptsUpdate) -> Chapter:
    return attr.evolve(
        chapter,
        manuscripts=update.manuscripts,
        uncertain_fragments=update.uncertain_fragments,
    )


def _create_manuscripts_edit(
    chapter: Chapter, update: ManuscriptsUpdate
) -> ChapterEdit:
    edited_outline = dump_outline(apply_manuscripts_update(chapter, update))

    def replace_manuscripts(outline: Outline) -> Outline:
        return {
            **outline,
            "manuscripts": edited_outline["manuscripts"],
            "uncertainFragments": edited_outline["uncertainFragments"],
        }

    return ChapterEdit(
        MANUSCRIPTS_SUFFIX,
        create_manuscripts_body(chapter, update),
        lambda writer, id_, revision, user: writer.save_manuscripts(
            id_, update, revision, user
        ),
        lambda corpus, id_, user: corpus.update_manuscripts(
            id_, update.manuscripts, update.uncertain_fragments, user
        ),
        replace_manuscripts,
    )


def create_manuscripts_edit(chapter: Chapter, step: int) -> ChapterEdit:
    return _create_manuscripts_edit(chapter, create_manuscripts_update(chapter, step))


def create_invalid_manuscripts_edit(chapter: Chapter) -> ChapterEdit:
    manuscript_with_unknown_reference = attr.evolve(
        chapter.manuscripts[0], references=(ReferenceFactory.build(),)
    )
    return _create_manuscripts_edit(
        chapter,
        ManuscriptsUpdate(
            (manuscript_with_unknown_reference, *chapter.manuscripts[1:]), ()
        ),
    )


IMPORT_EDITS = ChapterEditKind(
    IMPORT_SUFFIX, create_import_edit, create_invalid_import_edit
)
MANUSCRIPTS_EDITS = ChapterEditKind(
    MANUSCRIPTS_SUFFIX, create_manuscripts_edit, create_invalid_manuscripts_edit
)
CHAPTER_EDIT_KINDS: Sequence[ChapterEditKind] = (IMPORT_EDITS, MANUSCRIPTS_EDITS)


def post_edit(
    client: testing.TestClient,
    chapter: Chapter,
    request: ChapterEditRequest,
    query_string: str,
) -> testing.Result:
    result = client.simulate_post(
        create_chapter_url(chapter, request.suffix),
        body=request.body,
        query_string=query_string,
    )
    assert isinstance(result, testing.Result)
    return result
