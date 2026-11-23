from typing import List, Sequence, Tuple

import pytest
from pymongo.database import Database

from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.line import Line
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.lemmatization.infrastrcuture.mongo_suggestions_finder import (
    COLLECTION,
    aggregate_lemmas,
)
from ebl.tests.factories.corpus import (
    ChapterFactory,
    LineFactory,
    LineVariantFactory,
    ManuscriptFactory,
    ManuscriptLineFactory,
)
from ebl.tests.lemmatization.lemma_batch_support import (
    MANUSCRIPT_TOKENS,
    QUERIES,
    RECONSTRUCTION,
)
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.text_line import TextLine

WORDS: Sequence[str] = tuple(dict.fromkeys(word for word, _ in QUERIES))
SELECTION = {"$in": list(WORDS)}
Count = Tuple[str, Tuple[str, ...], int]


def create_other_line() -> Line:
    return LineFactory.build(
        variants=(
            LineVariantFactory.build(
                manuscripts=(ManuscriptLineFactory.build(manuscript_id=1),)
            ),
        )
    )


def create_chapter_with_other_lines() -> Chapter:
    return ChapterFactory.build(
        manuscripts=(ManuscriptFactory.build(id=1), ManuscriptFactory.build(id=2)),
        lines=(
            create_other_line(),
            LineFactory.build(
                variants=(
                    LineVariantFactory.build(
                        manuscripts=(ManuscriptLineFactory.build(manuscript_id=2),)
                    ),
                    LineVariantFactory.build(
                        reconstruction=RECONSTRUCTION,
                        manuscripts=(
                            ManuscriptLineFactory.build(manuscript_id=1),
                            ManuscriptLineFactory.build(
                                manuscript_id=2,
                                line=TextLine.of_iterable(
                                    LineNumber(2), MANUSCRIPT_TOKENS
                                ),
                            ),
                        ),
                    ),
                )
            ),
            create_other_line(),
        ),
    )


def is_selection(stage: dict) -> bool:
    return any(
        key.endswith(".cleanValue") and key != "tokens.cleanValue"
        for key in stage.get("$match", {})
    )


def remove_selections(pipeline: Sequence[dict]) -> List[dict]:
    return [
        {
            "$unionWith": {
                **stage["$unionWith"],
                "pipeline": remove_selections(stage["$unionWith"]["pipeline"]),
            }
        }
        if "$unionWith" in stage
        else stage
        for stage in pipeline
        if not is_selection(stage)
    ]


def count_lemmas(database: Database, pipeline: Sequence[dict]) -> List[Count]:
    return sorted(
        (result["_id"]["word"], tuple(result["_id"]["lemma"]), result["count"])
        for result in database[COLLECTION].aggregate(list(pipeline))
    )


@pytest.mark.parametrize("is_normalized", [False, True])
def test_selecting_chapters_lines_and_variants_first_does_not_change_the_counts(
    is_normalized: bool,
    database: Database,
    text_repository: MongoTextRepository,
    seeded_tokens: None,
) -> None:
    text_repository.create_chapter(create_chapter_with_other_lines())
    text_repository.create_chapter(
        ChapterFactory.build(
            manuscripts=(ManuscriptFactory.build(id=1),),
            lines=(create_other_line(),),
        )
    )
    pipeline = aggregate_lemmas(WORDS, is_normalized)
    unselected_pipeline = remove_selections(pipeline)

    counts = count_lemmas(database, pipeline)

    assert counts == count_lemmas(database, unselected_pipeline)
    assert counts
    assert len(unselected_pipeline) < len(pipeline)


@pytest.mark.parametrize(
    "union_index,path,array_count",
    [
        (0, "lines.variants.reconstruction", 2),
        (1, "lines.variants.manuscripts.line.content", 3),
    ],
)
def test_chapter_tokens_are_selected_before_and_after_every_unwind(
    union_index: int, path: str, array_count: int
) -> None:
    selection = {"$match": {f"{path}.cleanValue": SELECTION}}
    unions = [
        stage["$unionWith"]
        for stage in aggregate_lemmas(WORDS, False)
        if "$unionWith" in stage
    ]
    pipeline = unions[union_index]["pipeline"]
    unwinds = [index for index, stage in enumerate(pipeline) if "$unwind" in stage]

    assert unions[union_index]["coll"] == "chapters"
    assert pipeline[:2] == [selection, {"$project": {path: 1}}]
    assert len(unwinds) == array_count + 1
    assert [pipeline[index + 1] for index in unwinds[:-1]] == [selection] * array_count
    assert pipeline[-2:] == [
        {"$project": {"tokens": f"${path}"}},
        {"$unwind": "$tokens"},
    ]


def test_fragment_lines_are_selected_before_their_tokens_are_unwound() -> None:
    pipeline = aggregate_lemmas(WORDS, False)

    assert pipeline[2:4] == [
        {"$unwind": "$lines"},
        {"$match": {"lines.content.cleanValue": SELECTION}},
    ]
