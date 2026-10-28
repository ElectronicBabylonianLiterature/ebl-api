from typing import Sequence

import pytest

from ebl.sumerian_dictionary.domain.search_query import (
    Kind,
    SourceFilter,
    SumerianWordQuery,
)
from ebl.sumerian_dictionary.domain.sumerian_word import (
    AkkadianEquivalent,
    Epsd2Sense,
    Sources,
)
from ebl.sumerian_dictionary.domain.sumerian_word_links import Alias
from ebl.sumerian_dictionary.infrastructure.mongo_sumerian_word_repository import (
    MongoSumerianWordRepository,
)
from ebl.tests.factories.sumerian_dictionary import (
    Epsd2SourceFactory,
    SumerianWordFactory,
)
from ebl.tests.sumerian_dictionary.conftest import InsertWords


def _ids(
    repository: MongoSumerianWordRepository,
    text: str,
    kind: Kind = Kind.ALL,
    source: SourceFilter = SourceFilter.ANY,
) -> Sequence[str]:
    result = repository.search(SumerianWordQuery(text, kind, source))
    return [entry.id for entry in result.entries]


@pytest.mark.parametrize("query", ["", "   "])
def test_empty_query_finds_nothing(
    sumerian_word_repository: MongoSumerianWordRepository,
    insert_words: InsertWords,
    query: str,
) -> None:
    insert_words(SumerianWordFactory.build())

    result = sumerian_word_repository.search(SumerianWordQuery(query))

    assert (result.total, result.entries) == (0, ())


@pytest.mark.parametrize(
    "stored,typed",
    [
        ("šu", "su"),
        ("šu", "szu"),
        ("ṣa", "sa"),
        ("ṭu", "tu"),
        ("ḫa", "ha"),
        ("ĝar", "gar"),
        ("ĝar", "ŋar"),
        ("ŋar", "gar"),
        ("dug₄", "dug4"),
        ("tumₓ", "tumx"),
        ("Ĝeššar", "gessar"),
    ],
)
def test_folding_pairs_find_the_stored_form(
    sumerian_word_repository: MongoSumerianWordRepository,
    insert_words: InsertWords,
    stored: str,
    typed: str,
) -> None:
    insert_words(SumerianWordFactory.build(id="hit", citation_form=stored))

    assert _ids(sumerian_word_repository, typed) == ["hit"]


def test_ranks_order_the_results(
    sumerian_word_repository: MongoSumerianWordRepository, insert_words: InsertWords
) -> None:
    insert_words(
        SumerianWordFactory.build(
            id="text", epsd2_senses=(Epsd2Sense("1.", "kingship", "en"),)
        ),
        SumerianWordFactory.build(id="prefix", citation_form="kinga"),
        SumerianWordFactory.build(id="guide", guide_word="king"),
        SumerianWordFactory.build(id="exact", citation_form="king"),
        SumerianWordFactory.build(id="other", citation_form="lugal"),
    )

    assert _ids(sumerian_word_repository, "king") == [
        "exact",
        "guide",
        "prefix",
        "text",
    ]


def test_alias_match_sets_matched_alias(
    sumerian_word_repository: MongoSumerianWordRepository, insert_words: InsertWords
) -> None:
    alias = Alias("{ĝeš}sar", "see", "att-1", "exact", "attinger")
    insert_words(
        SumerianWordFactory.build(id="sar", citation_form="sar", aliases=(alias,))
    )

    result = sumerian_word_repository.search(SumerianWordQuery("ĝešsar"))

    assert [(entry.id, entry.matched_alias) for entry in result.entries] == [
        ("sar", "{ĝeš}sar")
    ]


def test_akkadian_equivalent_is_searched(
    sumerian_word_repository: MongoSumerianWordRepository, insert_words: InsertWords
) -> None:
    equivalent = AkkadianEquivalent("šarru I", "borger")
    insert_words(
        SumerianWordFactory.build(id="lugal", akkadian_equivalents=(equivalent,))
    )

    assert _ids(sumerian_word_repository, "šarru") == ["lugal"]


def test_prefiltered_but_unscored_documents_are_dropped(
    sumerian_word_repository: MongoSumerianWordRepository, insert_words: InsertWords
) -> None:
    insert_words(SumerianWordFactory.build(id="braced", citation_form="{ĝeš}sar"))

    result = sumerian_word_repository.search(SumerianWordQuery("gessar"))

    assert (result.total, result.entries) == (0, ())


@pytest.mark.parametrize(
    "kind,expected",
    [(Kind.ALL, ["noun", "name"]), (Kind.WORDS, ["noun"]), (Kind.NAMES, ["name"])],
)
def test_kind_filter(
    sumerian_word_repository: MongoSumerianWordRepository,
    insert_words: InsertWords,
    kind: Kind,
    expected: Sequence[str],
) -> None:
    insert_words(
        SumerianWordFactory.build(id="noun", citation_form="nin"),
        SumerianWordFactory.build(id="name", citation_form="nina", pos="DN"),
    )

    assert _ids(sumerian_word_repository, "nin", kind=kind) == expected


@pytest.mark.parametrize(
    "source,expected",
    [
        (SourceFilter.ANY, ["attinger", "epsd2"]),
        (SourceFilter.ATTINGER, ["attinger"]),
        (SourceFilter.EPSD2, ["epsd2"]),
    ],
)
def test_source_filter(
    sumerian_word_repository: MongoSumerianWordRepository,
    insert_words: InsertWords,
    source: SourceFilter,
    expected: Sequence[str],
) -> None:
    epsd2_only = Sources(epsd2=Epsd2SourceFactory.build())
    insert_words(
        SumerianWordFactory.build(id="attinger", citation_form="an"),
        SumerianWordFactory.build(id="epsd2", citation_form="ana", sources=epsd2_only),
    )

    assert _ids(sumerian_word_repository, "an", source=source) == expected


def test_limit_and_offset_slice_after_ranking(
    sumerian_word_repository: MongoSumerianWordRepository, insert_words: InsertWords
) -> None:
    insert_words(
        *(
            SumerianWordFactory.build(id=f"w{length}", citation_form="a" * length)
            for length in range(1, 6)
        )
    )

    result = sumerian_word_repository.search(SumerianWordQuery("a", limit=2, offset=1))

    assert result.total == 5
    assert [entry.id for entry in result.entries] == ["w2", "w3"]


def test_unmanaged_documents_are_not_searched(
    sumerian_word_repository: MongoSumerianWordRepository,
) -> None:
    sumerian_word_repository._collection.insert_one({"_id": "x", "citationForm": "a"})

    assert sumerian_word_repository.search(SumerianWordQuery("a")).total == 0


@pytest.mark.parametrize("query", ["a.b(", "[x]", "*", "a b", '"lu"'])
def test_special_characters_are_literal(
    sumerian_word_repository: MongoSumerianWordRepository,
    insert_words: InsertWords,
    query: str,
) -> None:
    insert_words(SumerianWordFactory.build(id="literal", citation_form=query))

    assert _ids(sumerian_word_repository, query) == ["literal"]
