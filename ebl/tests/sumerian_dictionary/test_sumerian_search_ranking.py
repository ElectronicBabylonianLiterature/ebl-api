from typing import Mapping

import pytest

from ebl.sumerian_dictionary.infrastructure.sumerian_search_ranking import (
    MatchRank,
    SumerianRelevanceRanker,
    fold,
)


def candidate(**fields: object) -> Mapping[str, object]:
    return {
        "_id": "o0000001",
        "citationForm": "",
        "guideWord": "",
        "homonym": "",
        "aliasForms": [],
        "senseMeanings": [],
        "akkadianWordIds": [],
        "hasAttinger": False,
        "attestationCount": 0,
        **fields,
    }


@pytest.mark.parametrize(
    "stored,typed",
    [
        ("šu", "su"),
        ("ṣa", "sa"),
        ("ṭu", "tu"),
        ("ḫa", "ha"),
        ("ĝar", "gar"),
        ("ĝar", "ŋar"),
        ("dug₄", "dug4"),
        ("tumₓ", "tumx"),
        ("šu", "szu"),
        ("ṣa", "s,a"),
        ("ṭu", "t,u"),
        ("ŠU", "šu"),
        ("é", "e"),
    ],
)
def test_folding_pairs_meet(stored: str, typed: str) -> None:
    assert fold(stored) == fold(typed)


@pytest.mark.parametrize(
    "query,document,expected",
    [
        ("Lugal", candidate(citationForm="lugal"), MatchRank.CITATION_FORM_AS_TYPED),
        ("dug4", candidate(citationForm="dug₄"), MatchRank.CITATION_FORM_FOLDED),
        (
            "gessar",
            candidate(citationForm="sar", aliasForms=["{ĝeš}sar"]),
            MatchRank.ALIAS,
        ),
        (
            "{ges}sar",
            candidate(citationForm="sar", aliasForms=["{ĝeš}sar"]),
            MatchRank.ALIAS,
        ),
        (
            "king",
            candidate(citationForm="lugal", guideWord="king"),
            MatchRank.GUIDE_WORD,
        ),
        ("lu", candidate(citationForm="lugal"), MatchRank.CITATION_FORM_PREFIX),
        ("ga", candidate(citationForm="lugal"), MatchRank.CITATION_FORM_SUBSTRING),
        (
            "king",
            candidate(citationForm="lugal", senseMeanings=["the king, ruler"]),
            MatchRank.WHOLE_WORD_IN_TEXT,
        ),
        ("great", candidate(guideWord="great king"), MatchRank.WHOLE_WORD_IN_TEXT),
        ("šarru", candidate(akkadianWordIds=["šarru I"]), MatchRank.WHOLE_WORD_IN_TEXT),
        (
            "kin",
            candidate(citationForm="lugal", senseMeanings=["kingship"]),
            MatchRank.SUBSTRING_IN_TEXT,
        ),
    ],
)
def test_each_rank(
    query: str, document: Mapping[str, object], expected: MatchRank
) -> None:
    assert SumerianRelevanceRanker(query).rank(document) == expected


def test_no_match_has_no_rank() -> None:
    assert SumerianRelevanceRanker("zzz").rank(candidate(citationForm="lugal")) is None


def test_alias_hit_names_the_alias_as_stored() -> None:
    document = candidate(citationForm="gub", aliasForms=["su₈-ba", "su₈-g"])

    assert SumerianRelevanceRanker("su8-g").alias_hit(document) == "su₈-g"


def test_alias_hit_is_empty_when_the_citation_form_matches() -> None:
    document = candidate(citationForm="sar", aliasForms=["sar"])

    assert SumerianRelevanceRanker("sar").alias_hit(document) == ""


def test_first_alias_wins_for_the_same_key() -> None:
    document = candidate(citationForm="sar", aliasForms=["{ĝeš}sar", "ĝešsar"])

    assert SumerianRelevanceRanker("ĝešsar").alias_hit(document) == "{ĝeš}sar"


def test_folded_query_strips_and_lowers() -> None:
    assert SumerianRelevanceRanker("  Dug4 ").folded_query == "dug4"


def _sorted_ids(query: str, *documents: Mapping[str, object]) -> list:
    ranker = SumerianRelevanceRanker(query)
    ranked = [(ranker.rank(document), document) for document in documents]
    return [
        document["_id"]
        for rank, document in sorted(
            ((rank, document) for rank, document in ranked if rank is not None),
            key=lambda pair: ranker.key(*pair),
        )
    ]


def test_rank_wins_over_tie_breaks() -> None:
    prefix = candidate(_id="prefix", citationForm="lugala", hasAttinger=True)
    exact = candidate(_id="exact", citationForm="lugal")

    assert _sorted_ids("lugal", prefix, exact) == ["exact", "prefix"]


def test_attinger_entries_first() -> None:
    epsd2 = candidate(_id="epsd2", citationForm="lugala", attestationCount=99)
    attinger = candidate(_id="attinger", citationForm="lugalb", hasAttinger=True)

    assert _sorted_ids("lugal", epsd2, attinger) == ["attinger", "epsd2"]


def test_higher_attestation_count_first() -> None:
    rare = candidate(_id="rare", citationForm="lugala", attestationCount=1)
    common = candidate(_id="common", citationForm="lugalb", attestationCount=9)

    assert _sorted_ids("lugal", rare, common) == ["common", "rare"]


def test_shorter_citation_form_first() -> None:
    long = candidate(_id="long", citationForm="lugalaa")
    short = candidate(_id="short", citationForm="lugala")

    assert _sorted_ids("lugal", long, short) == ["short", "long"]


def test_homonym_numeral_order() -> None:
    documents = [
        candidate(_id=homonym or "none", citationForm="lugala", homonym=homonym)
        for homonym in ("X", "II", "IV", "", "I", "IX")
    ]

    assert _sorted_ids("lugal", *documents) == ["none", "I", "II", "IV", "IX", "X"]


def test_unknown_homonym_sorts_with_empty_then_by_id() -> None:
    documents = [
        candidate(_id="b", citationForm="lugala", homonym="XI"),
        candidate(_id="a", citationForm="lugala", homonym=""),
    ]

    assert _sorted_ids("lugal", *documents) == ["a", "b"]


def test_malformed_fields_are_read_as_empty() -> None:
    document = candidate(citationForm=None, aliasForms=None, attestationCount="9")

    assert SumerianRelevanceRanker("x").rank(document) is None
