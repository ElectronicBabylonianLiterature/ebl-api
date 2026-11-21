import json
from typing import Any, Dict, Iterator, Sequence

import attr
import pytest

from ebl.common.domain.stage import Stage
from ebl.corpus.domain.chapter import Chapter, Classification
from ebl.corpus.domain.chapter_outline import (
    ChapterOutline,
    LineOutline,
    LineVariantOutline,
    ManuscriptOutline,
)
from ebl.corpus.domain.chapter_revision import LEGACY_REVISION
from ebl.corpus.domain.lines_page import LinesPage
from ebl.corpus.web.chapter_outline_schemas import (
    LINE_TOKEN_FIELDS,
    ChapterOutlineSchema,
    create_lines_page_schema,
)
from ebl.corpus.web.chapter_schemas import ApiLineSchema
from ebl.tests.corpus.outline_support import (
    OUTLINE_CHAPTER_KEYS,
    create_expected_outline_line,
    create_outline_chapter,
    dump_outline,
    dump_to_dict,
    remove_token_fields,
)
from ebl.tests.corpus.support import create_chapter_dto
from ebl.tests.factories.corpus import ChapterFactory
from ebl.tests.transliteration.storage_test_helpers import has_key
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.domain.text_id import TextId

REVISION = "6aff54f935de52a4db0c81df"
OUTLINE = ChapterOutline(
    TextId(Genre.LITERATURE, 1, 2),
    Classification.ANCIENT,
    Stage.STANDARD_BABYLONIAN,
    "",
    "I",
    1,
    ("K.1",),
    (ManuscriptOutline(1, "NinNA1a", "K.5419.C", ""),),
    (
        LineOutline(
            0,
            "1",
            False,
            True,
            "#tr.en: When on high\n#tr.ar: bar",
            (
                LineVariantOutline(
                    "%n enūma | eliš\n#note: a note\n// (name 7)", (1, 5, 9)
                ),
            ),
        ),
    ),
    REVISION,
)
OUTLINE_DTO = {
    "textId": {"genre": "L", "category": 1, "index": 2},
    "classification": "Ancient",
    "stage": "Standard Babylonian",
    "version": "",
    "name": "I",
    "order": 1,
    "uncertainFragments": ["K.1"],
    "manuscripts": [
        {"id": 1, "siglum": "NinNA1a", "museumNumber": "K.5419.C", "accession": ""}
    ],
    "lines": [
        {
            "index": 0,
            "number": "1",
            "isSecondLineOfParallelism": False,
            "isBeginningOfSection": True,
            "translation": "#tr.en: When on high\n#tr.ar: bar",
            "variants": [
                {
                    "reconstruction": "%n enūma | eliš\n#note: a note\n// (name 7)",
                    "manuscriptIds": [1, 5, 9],
                }
            ],
        }
    ],
    "revision": REVISION,
}


def iterate_arrays(value: object) -> Iterator[Sequence[object]]:
    if isinstance(value, dict):
        for item in value.values():
            yield from iterate_arrays(item)
    elif isinstance(value, list):
        yield value
        for item in value:
            yield from iterate_arrays(item)


def dump_lines_page(page: LinesPage, include_tokens: bool) -> Dict[str, Any]:
    return dump_to_dict(create_lines_page_schema(include_tokens), page)


def test_dump_chapter_outline() -> None:
    assert ChapterOutlineSchema().dump(OUTLINE) == OUTLINE_DTO


def test_dump_chapter_outline_without_revision() -> None:
    outline = attr.evolve(OUTLINE, revision=LEGACY_REVISION)

    assert ChapterOutlineSchema().dump(outline) == {**OUTLINE_DTO, "revision": "legacy"}


def test_dumped_chapter_outline_is_json() -> None:
    dto = dump_outline(ChapterFactory.build())

    assert json.loads(json.dumps(dto)) == dto


@pytest.mark.parametrize("chapter", [create_outline_chapter(), ChapterFactory.build()])
def test_dumped_chapter_outline_matches_api_chapter(chapter: Chapter) -> None:
    api_chapter = create_chapter_dto(chapter)
    dto = dump_outline(chapter)

    assert {key: dto[key] for key in OUTLINE_CHAPTER_KEYS} == {
        key: api_chapter[key] for key in OUTLINE_CHAPTER_KEYS
    }
    assert dto["lines"] == [
        create_expected_outline_line(index, line)
        for index, line in enumerate(api_chapter["lines"])
    ]


def test_dumped_manuscripts_match_api_manuscripts() -> None:
    chapter = create_outline_chapter()

    assert dump_outline(chapter)["manuscripts"] == [
        {
            "id": manuscript["id"],
            "siglum": str(chapter.manuscripts[index].siglum),
            "museumNumber": manuscript["museumNumber"],
            "accession": manuscript["accession"],
        }
        for index, manuscript in enumerate(create_chapter_dto(chapter)["manuscripts"])
    ]


def test_dumped_manuscript_ids_refer_to_dumped_manuscripts() -> None:
    dto = dump_outline(create_outline_chapter())
    manuscript_ids = [manuscript["id"] for manuscript in dto["manuscripts"]]

    assert all(
        manuscript_id in manuscript_ids
        for line in dto["lines"]
        for variant in line["variants"]
        for manuscript_id in variant["manuscriptIds"]
    )


def test_dumped_arrays_hold_one_data_type() -> None:
    arrays = list(iterate_arrays(dump_outline(create_outline_chapter())))

    assert len(arrays) == 10
    assert all(len({type(item) for item in array}) <= 1 for array in arrays)


def test_dump_lines_page_with_tokens() -> None:
    chapter = create_outline_chapter()
    page = LinesPage(len(chapter.lines), 1, 2, chapter.lines[1:3], REVISION)
    dto = dump_lines_page(page, True)

    assert dto == {
        "total": 3,
        "offset": 1,
        "limit": 2,
        "lines": create_chapter_dto(chapter)["lines"][1:3],
        "revision": REVISION,
    }
    assert has_key(dto, "reconstructionTokens") and has_key(dto, "atfTokens")


def test_dump_lines_page_without_tokens() -> None:
    chapter = create_outline_chapter()
    page = LinesPage(len(chapter.lines), 0, 10, chapter.lines, LEGACY_REVISION)
    dto = dump_lines_page(page, False)

    assert dto == {
        "total": 3,
        "offset": 0,
        "limit": 10,
        "lines": [
            remove_token_fields(line) for line in create_chapter_dto(chapter)["lines"]
        ],
        "revision": "legacy",
    }
    assert dto["lines"] == ApiLineSchema(exclude=LINE_TOKEN_FIELDS).dump(
        chapter.lines, many=True
    )
    assert not has_key(dto, "reconstructionTokens") and not has_key(dto, "atfTokens")


def test_lines_page_schemas_do_not_share_excluded_fields() -> None:
    chapter = create_outline_chapter()
    page = LinesPage(len(chapter.lines), 0, 10, chapter.lines, LEGACY_REVISION)
    dump_lines_page(page, False)

    assert dump_lines_page(page, True)["lines"] == create_chapter_dto(chapter)["lines"]


@pytest.mark.parametrize("include_tokens", [True, False])
def test_dump_empty_lines_page(include_tokens: bool) -> None:
    assert dump_lines_page(LinesPage(3, 7, 50, (), REVISION), include_tokens) == {
        "total": 3,
        "offset": 7,
        "limit": 50,
        "lines": [],
        "revision": REVISION,
    }
