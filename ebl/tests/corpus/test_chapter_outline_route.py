from functools import partial
from typing import Any, Callable, Dict, cast

import attr
import falcon
import pytest
from falcon import testing

from ebl.common.domain.stage import Stage
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_revision import LEGACY_REVISION
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.tests.corpus.outline_support import (
    OUTLINE_CHAPTER_KEYS,
    create_chapter_with_lines,
    create_expected_outline_line,
    create_outline_chapter,
    dump_outline,
)
from ebl.tests.corpus.support import (
    create_chapter_dto,
    create_chapter_url,
    simulate_get,
)
from ebl.tests.factories.corpus import ChapterFactory
from ebl.transliteration.domain.line_number import LineNumber

LINE_COUNT = 12
STANDARD_BABYLONIAN = Stage.STANDARD_BABYLONIAN.long_name


def create_expected_outline(
    chapter: Chapter, revision: str = LEGACY_REVISION
) -> Dict[str, Any]:
    chapter_dto = create_chapter_dto(chapter)
    sigla = {
        manuscript.id: str(manuscript.siglum) for manuscript in chapter.manuscripts
    }
    return {
        **{key: chapter_dto[key] for key in OUTLINE_CHAPTER_KEYS},
        "manuscripts": [
            {
                "id": manuscript["id"],
                "siglum": sigla[manuscript["id"]],
                "museumNumber": manuscript["museumNumber"],
                "accession": manuscript["accession"],
            }
            for manuscript in chapter_dto["manuscripts"]
        ],
        "lines": [
            create_expected_outline_line(index, line)
            for index, line in enumerate(chapter_dto["lines"])
        ],
        "revision": revision,
    }


def get_outline(client: testing.TestClient, chapter: Chapter) -> testing.Result:
    return simulate_get(client, create_chapter_url(chapter, "/outline"))


@pytest.fixture
def chapter(text_repository: MongoTextRepository) -> Chapter:
    chapter = create_outline_chapter()
    text_repository.create_chapter(chapter)
    return chapter


@pytest.mark.parametrize(
    "create_chapter",
    [
        create_outline_chapter,
        partial(create_chapter_with_lines, LINE_COUNT),
        ChapterFactory.build,
    ],
)
def test_get_outline(
    client: testing.TestClient,
    text_repository: MongoTextRepository,
    create_chapter: Callable[[], Chapter],
) -> None:
    chapter = create_chapter()
    text_repository.create_chapter(chapter)

    result = get_outline(client, chapter)

    assert result.status == falcon.HTTP_OK
    assert result.json == create_expected_outline(chapter)
    assert result.json == dump_outline(chapter)


def test_get_outline_follows_the_contract(
    client: testing.TestClient, chapter: Chapter
) -> None:
    outline = cast(Dict[str, Any], get_outline(client, chapter).json)
    variants = outline["lines"][0]["variants"]

    assert outline["textId"] == {
        "genre": chapter.text_id.genre.value,
        "category": chapter.text_id.category,
        "index": chapter.text_id.index,
    }
    assert outline["stage"] == chapter.stage.long_name
    assert outline["uncertainFragments"] == ["K.1", "BM.2.a"]
    assert outline["manuscripts"] == [
        {
            "id": 1,
            "siglum": str(chapter.manuscripts[0].siglum),
            "museumNumber": "K.5419.C",
            "accession": "",
        },
        {
            "id": 5,
            "siglum": str(chapter.manuscripts[1].siglum),
            "museumNumber": "",
            "accession": "A.12",
        },
    ]
    assert [line["index"] for line in outline["lines"]] == [0, 1, 2]
    assert [line["number"] for line in outline["lines"]] == ["1", "2", "3-4'"]
    assert outline["lines"][0]["translation"] == "#tr.en.(2): When on high\n#tr.ar: bar"
    assert [variant["manuscriptIds"] for variant in variants] == [[1, 5], []]
    assert variants[0]["reconstruction"].endswith("\n#note: a note\n// (name 7)")
    assert outline["revision"] == "legacy"


def test_get_outline_as_guest(
    guest_client: testing.TestClient, chapter: Chapter
) -> None:
    result = get_outline(guest_client, chapter)

    assert result.status == falcon.HTTP_OK
    assert result.json == create_expected_outline(chapter)


def test_get_outline_is_not_cached(
    cached_client: testing.TestClient,
    text_repository: MongoTextRepository,
    chapter: Chapter,
) -> None:
    first_result = get_outline(cached_client, chapter)
    updated_chapter = attr.evolve(
        chapter,
        lines=(
            *chapter.lines[:2],
            attr.evolve(chapter.lines[2], number=LineNumber(9, True)),
        ),
    )
    text_repository.update(chapter.id_, updated_chapter)

    second_result = get_outline(cached_client, chapter)
    revision = text_repository.find_chapter_revision(chapter.id_)

    assert first_result.json == create_expected_outline(chapter)
    assert second_result.json == create_expected_outline(updated_chapter, revision)
    assert second_result.json != create_expected_outline(chapter, revision)
    assert revision != LEGACY_REVISION


@pytest.mark.parametrize(
    "create_missing_chapter",
    [
        lambda chapter: attr.evolve(chapter, name=f"{chapter.name} missing"),
        lambda chapter: attr.evolve(
            chapter,
            stage=next(stage for stage in Stage if stage is not chapter.stage),
        ),
        lambda chapter: attr.evolve(
            chapter, text_id=attr.evolve(chapter.text_id, index=99999)
        ),
    ],
)
def test_get_outline_of_unknown_chapter(
    client: testing.TestClient,
    chapter: Chapter,
    create_missing_chapter: Callable[[Chapter], Chapter],
) -> None:
    result = get_outline(client, create_missing_chapter(chapter))

    assert result.status == falcon.HTTP_NOT_FOUND


@pytest.mark.parametrize(
    "url",
    [
        "/texts/L/1/1/chapters/invalid/any/outline",
        f"/texts/L/1/invalid/chapters/{STANDARD_BABYLONIAN}/any/outline",
        f"/texts/L/invalid/1/chapters/{STANDARD_BABYLONIAN}/any/outline",
        f"/texts/invalid/1/1/chapters/{STANDARD_BABYLONIAN}/any/outline",
    ],
)
def test_get_outline_with_invalid_id(client: testing.TestClient, url: str) -> None:
    result = simulate_get(client, url)

    assert result.status == falcon.HTTP_NOT_FOUND


def test_outline_is_read_only(client: testing.TestClient, chapter: Chapter) -> None:
    result = client.simulate_post(create_chapter_url(chapter, "/outline"), body="{}")

    assert result.status == falcon.HTTP_METHOD_NOT_ALLOWED
