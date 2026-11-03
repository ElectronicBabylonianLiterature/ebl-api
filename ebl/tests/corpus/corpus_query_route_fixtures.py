from typing import List, Optional
import attr
from ebl.corpus.application.id_schemas import TextIdSchema
from ebl.corpus.domain.chapter import Chapter
from ebl.dictionary.domain.word import WordId
from ebl.tests.corpus.mongo_text_repository_fixtures import LITERATURE_TEXT
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


CHAPTER_WITH_SIGNS_AND_LEMMAS = attr.evolve(
    CHAPTER_WITH_SIGNS,
    manuscripts=(*CHAPTER_WITH_SIGNS.manuscripts, LEMMA_MANUSCRIPT),
    lines=(*CHAPTER_WITH_SIGNS.lines, *CHAPTER_WITH_LEMMA.lines),  # pyre-ignore[60]
)


def query_response_of(chapter: Chapter, lines: List[int], variants: List[int]) -> dict:
    return {
        "items": [query_item_of(chapter, lines=lines, variants=variants)],
        "matchCountTotal": len(lines),
    }
