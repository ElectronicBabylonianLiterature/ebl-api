from typing import Sequence

import pytest

from ebl.sumerian_dictionary.domain.sumerian_word import Epsd2Sense, Rendering
from ebl.sumerian_dictionary.domain.sumerian_word_summary import SumerianWordSummary
from ebl.sumerian_dictionary.infrastructure.mongo_sumerian_word_repository import (
    MongoSumerianWordRepository,
)
from ebl.tests.factories.sumerian_dictionary import (
    SumerianWordFactory,
    build_complete_word,
)
from ebl.tests.sumerian_dictionary.conftest import InsertWords


def _rendering(
    spelling: str, source: str, kind: str, cuneiform: str, complete: bool = True
) -> Rendering:
    return Rendering(spelling, source, kind, (cuneiform, "other"), complete)


def _summary(repository: MongoSumerianWordRepository, id_: str) -> SumerianWordSummary:
    return repository.find_summaries([id_])[0]


def test_summary_of_a_complete_word(
    sumerian_word_repository: MongoSumerianWordRepository, insert_words: InsertWords
) -> None:
    word = build_complete_word()
    insert_words(word)

    assert _summary(sumerian_word_repository, word.id) == SumerianWordSummary(
        id=word.id,
        citation_form=word.citation_form,
        homonym="I",
        guide_word="word",
        pos="N",
        attinger_pos="N",
        language="EMESAL",
        cuneiform="",
        french_senses=("roi",),
        english_senses=("king",),
        has_attinger=True,
        has_epsd2=True,
        epsd2_form_count=1,
        akkadian_count=1,
        citation_count=1,
        compound_count=2,
        cross_reference_count=1,
        has_emesal=True,
        attestation_count=1200,
    )


def test_summary_of_an_empty_word(
    sumerian_word_repository: MongoSumerianWordRepository, insert_words: InsertWords
) -> None:
    insert_words(SumerianWordFactory.build(id="empty"))

    summary = _summary(sumerian_word_repository, "empty")

    assert (summary.cuneiform, summary.has_epsd2, summary.has_emesal) == (
        "",
        False,
        False,
    )
    assert (summary.french_senses, summary.english_senses) == ((), ())
    assert summary.attestation_count == 0


@pytest.mark.parametrize(
    "renderings,expected",
    [
        ((_rendering("a", "attinger", "key", "𒀀"),), "𒀀"),
        (
            (
                _rendering("a", "attinger", "key", "𒀉", complete=False),
                _rendering("a", "attinger", "key", "𒀀"),
            ),
            "𒀀",
        ),
        (
            (
                _rendering("lugal", "epsd2", "form", "𒈗"),
                _rendering("a", "attinger", "key", "𒀀"),
            ),
            "𒀀",
        ),
        ((_rendering("lugal", "epsd2", "form", "𒈗"),), "𒈗"),
        ((_rendering("lugal", "attinger", "variant", "𒈗"),), ""),
        ((_rendering("lugal-e", "epsd2", "form", "𒈗"),), ""),
        ((_rendering("lugal", "epsd2", "form", "𒈗", complete=False),), ""),
    ],
)
def test_summary_cuneiform(
    sumerian_word_repository: MongoSumerianWordRepository,
    insert_words: InsertWords,
    renderings: Sequence[Rendering],
    expected: str,
) -> None:
    insert_words(
        SumerianWordFactory.build(id="w", citation_form="lugal", renderings=renderings)
    )

    assert _summary(sumerian_word_repository, "w").cuneiform == expected


def test_summary_keeps_the_first_four_english_senses(
    sumerian_word_repository: MongoSumerianWordRepository, insert_words: InsertWords
) -> None:
    senses = tuple(Epsd2Sense(f"{n}.", f"sense {n}", "en") for n in range(1, 7))
    insert_words(SumerianWordFactory.build(id="w", epsd2_senses=senses))

    assert _summary(sumerian_word_repository, "w").english_senses == (
        "sense 1",
        "sense 2",
        "sense 3",
        "sense 4",
    )


def test_find_summaries_keeps_the_order_asked_and_skips_missing(
    sumerian_word_repository: MongoSumerianWordRepository, insert_words: InsertWords
) -> None:
    insert_words(*(SumerianWordFactory.build(id=id_) for id_ in ("a", "b", "c")))
    sumerian_word_repository._collection.insert_one({"_id": "legacy"})

    summaries = sumerian_word_repository.find_summaries(["c", "gone", "a", "legacy"])

    assert [summary.id for summary in summaries] == ["c", "a"]


def test_find_summaries_of_nothing(
    sumerian_word_repository: MongoSumerianWordRepository,
) -> None:
    assert sumerian_word_repository.find_summaries([]) == ()
