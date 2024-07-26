from typing import List, Optional
import attr
import falcon
import pytest
from ebl.corpus.application.id_schemas import TextIdSchema
from ebl.corpus.domain.chapter import Chapter
from ebl.dictionary.domain.word import WordId
from ebl.tests.corpus.test_mongo_text_repository import LITERATURE_TEXT
from ebl.tests.factories.corpus import (
    ChapterFactory,
    LineFactory,
    LineVariantFactory,
    ManuscriptFactory,
    ManuscriptLineFactory,
)
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.text_id import TextId
from ebl.transliteration.domain.tokens import ValueToken


def word_with_lemma(lemmaId: str) -> AkkadianWord:
    return AkkadianWord.of(
        (ValueToken.of(lemmaId.split()[0]),),
        unique_lemma=(WordId(lemmaId),),
    )


LEMMA_MANUSCRIPT = ManuscriptFactory.build()
VARIANT_1 = LineVariantFactory.build(
    manuscripts=(),
    reconstruction=(
        word_with_lemma("ina I"),
        word_with_lemma("qanû I"),
    ),
)
LINE_1 = LineFactory.build(
    variants=(
        attr.evolve(
            VARIANT_1,
            manuscripts=(
                ManuscriptLineFactory.build(manuscript_id=LEMMA_MANUSCRIPT.id),
            ),
        ),
    ),
)
LINE_2 = LineFactory.build(
    variants=(
        attr.evolve(
            VARIANT_1,
            reconstruction=(
                word_with_lemma("bamātu I"),
                word_with_lemma("qanû I"),
            ),
            manuscripts=(),
        ),
    ),
)
LINE_3 = LineFactory.build(
    variants=(
        attr.evolve(
            VARIANT_1,
            reconstruction=(
                word_with_lemma("mu I"),
                word_with_lemma("u I"),
            ),
            manuscripts=(),
        ),
    ),
)
CHAPTER_WITH_LEMMA: Chapter = ChapterFactory.build(
    text_id=LITERATURE_TEXT.id,
    manuscripts=(LEMMA_MANUSCRIPT,),
    lines=(LINE_1, LINE_2, LINE_3),
)


def query_item_of(
    chapter: Chapter,
    lines: Optional[List[int]] = None,
    variants: Optional[List[int]] = None,
) -> dict:
    return {
        "lines": lines or [],
        "variants": variants or [],
        "matchCount": len(lines or []),
        "name": chapter.name,
        "stage": chapter.stage.long_name,
        "textId": TextIdSchema().dump(chapter.text_id),
    }


@pytest.mark.parametrize(
    "lemma_operator,lemmas,expected_lines,expected_variants",
    [
        ("and", "ina I+qanû I", [0, 1], [0, 0]),
        ("or", "ginâ I+bamātu I+mu I", [1, 2], [0, 0]),
        ("line", "mu I+u I", [2], [0]),
        ("phrase", "mu I+u I", [2], [0]),
    ],
)
def test_query_chapter_lemmas(
    client, text_repository, lemma_operator, lemmas, expected_lines, expected_variants
):
    text_repository.create_chapter(CHAPTER_WITH_LEMMA)

    result = client.simulate_get(
        "/corpus/query",
        params={"lemmaOperator": lemma_operator, "lemmas": lemmas},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == {
        "items": [
            query_item_of(
                CHAPTER_WITH_LEMMA,
                lines=expected_lines,
                variants=expected_variants,
            )
        ],
        "matchCountTotal": len(expected_lines),
    }


SIGNS = [
    "X ABZ411 ABZ11 ABZ41",
    "X X X TI BA",
    "MA ŠU X\nTI BA X",
]
MANUSCRIPTS = ManuscriptFactory.build_batch(3)
VARIANT_LINES = [
    [
        LineVariantFactory.build(
            manuscripts=(ManuscriptLineFactory.build(manuscript_id=MANUSCRIPTS[0].id),),
        )
    ],
    [
        LineVariantFactory.build(
            manuscripts=(),
        )
    ],
    [
        LineVariantFactory.build(
            manuscripts=(),
        ),
        LineVariantFactory.build(
            manuscripts=tuple(
                ManuscriptLineFactory.build(manuscript_id=manuscript.id)
                for manuscript in MANUSCRIPTS[1:]
            ),
        ),
    ],
    [
        LineVariantFactory.build(
            manuscripts=(ManuscriptLineFactory.build(manuscript_id=MANUSCRIPTS[2].id),),
        )
    ],
]
LINES = [
    LineFactory.build(
        variants=tuple(variants),
    )
    for variants in VARIANT_LINES
]

CHAPTER_WITH_SIGNS: Chapter = ChapterFactory.build(
    manuscripts=tuple(MANUSCRIPTS),
    lines=tuple(LINES),
    signs=SIGNS,
    text_id=TextId(Genre.LITERATURE, 42, 1),
)


@pytest.mark.parametrize(
    "transliteration,expected_lines,expected_variants",
    [
        ("bul bansur", [0], [0]),
        ("ti", [2, 3], [1, 0]),
        ("x", [0, 2, 3], [0, 1, 0]),
        ("šu", [2], [1]),
        ("ma šu\nba", [2, 3], [1, 0]),
    ],
)
def test_query_chapter_signs(
    client,
    text_repository,
    sign_repository,
    signs,
    transliteration,
    expected_lines,
    expected_variants,
):
    for sign in signs:
        sign_repository.create(sign)
    text_repository.create_chapter(CHAPTER_WITH_SIGNS)

    result = client.simulate_get(
        "/corpus/query",
        params={"transliteration": transliteration},
    )

    expected = {
        "items": [
            query_item_of(
                CHAPTER_WITH_SIGNS, lines=expected_lines, variants=expected_variants
            )
        ],
        "matchCountTotal": len(expected_lines),
    }

    assert result.status == falcon.HTTP_OK
    assert result.json == expected


CHAPTER_WITH_SIGNS_AND_LEMMAS = attr.evolve(
    CHAPTER_WITH_SIGNS,
    manuscripts=(*CHAPTER_WITH_SIGNS.manuscripts, LEMMA_MANUSCRIPT),
    lines=(*CHAPTER_WITH_SIGNS.lines, *CHAPTER_WITH_LEMMA.lines),  # pyre-ignore[60]
)


@pytest.mark.parametrize(
    "transliteration,lemmas,lemma_operator,expected_lines,expected_variants",
    [
        ("bul bansur", "ina I", "and", [0, 4], [0, 0]),
        ("ma šu\nba", "bamātu I+qanû I", "phrase", [2, 3, 5], [1, 0, 0]),
        ("ti", "u I+mu I", "line", [2, 3, 6], [1, 0, 0]),
    ],
)
def test_query_chapter_lemmas_and_signs(
    client,
    text_repository,
    sign_repository,
    signs,
    transliteration,
    lemmas,
    lemma_operator,
    expected_lines,
    expected_variants,
):
    for sign in signs:
        sign_repository.create(sign)

    text_repository.create_chapter(CHAPTER_WITH_SIGNS_AND_LEMMAS)

    result = client.simulate_get(
        "/corpus/query",
        params={
            "transliteration": transliteration,
            "lemmas": lemmas,
            "lemmaOperator": lemma_operator,
        },
    )

    expected = {
        "items": [
            query_item_of(
                CHAPTER_WITH_SIGNS_AND_LEMMAS,
                lines=expected_lines,
                variants=expected_variants,
            )
        ],
        "matchCountTotal": len(expected_lines),
    }

    assert result.status == falcon.HTTP_OK
    assert result.json == expected
