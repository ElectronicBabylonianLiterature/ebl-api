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
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
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
CHAPTER_WITH_QUERY_LEMMA: Chapter = ChapterFactory.build(
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
        "stage": chapter.stage.value,
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
    text_repository.create_chapter(CHAPTER_WITH_QUERY_LEMMA)

    result = client.simulate_get(
        "/corpus/query",
        params={"lemmaOperator": lemma_operator, "lemmas": lemmas},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == {
        "items": [
            query_item_of(
                CHAPTER_WITH_QUERY_LEMMA,
                lines=expected_lines,
                variants=expected_variants,
            )
        ],
        "matchCountTotal": len(expected_lines),
    }
