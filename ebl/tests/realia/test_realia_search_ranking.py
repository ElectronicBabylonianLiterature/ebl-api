from typing import Dict

from ebl.realia.infrastructure.realia_search_ranking import (
    NO_MATCH_RANK,
    RealiaRelevanceRanker,
)


def _document(identifier: str, related_terms=()) -> dict:
    return {"_id": identifier, "relatedTerms": list(related_terms)}


def _doc(**fields: object) -> Dict[str, object]:
    return dict(fields)


def test_ranks_exact_id_first() -> None:
    ranker = RealiaRelevanceRanker("Marduk")
    documents = [
        _document("Amêl-Marduk"),
        _document("Marduk A. I. Philologisch"),
        _document("Marduk"),
    ]
    documents.sort(key=ranker.key)
    assert [document["_id"] for document in documents] == [
        "Marduk",
        "Marduk A. I. Philologisch",
        "Amêl-Marduk",
    ]


def test_id_match_beats_related_term_match() -> None:
    ranker = RealiaRelevanceRanker("Marduk")
    id_match = _document("Dûr-Marduk")
    term_match = _document("Esagil", related_terms=("Marduk",))
    assert ranker.key(id_match)[0] < ranker.key(term_match)[0]


def test_related_term_tiers() -> None:
    ranker = RealiaRelevanceRanker("Pferd")
    exact = _document("Equus", related_terms=("Pferd",))
    prefix = _document("Equs", related_terms=("Pferdchen",))
    substring = _document("Equ", related_terms=("Reitpferd",))
    assert ranker.key(exact)[0] < ranker.key(prefix)[0] < ranker.key(substring)[0]


def test_alphabetical_tiebreak_within_rank() -> None:
    ranker = RealiaRelevanceRanker("Marduk")
    documents = [_document("Marduk-zakir"), _document("Marduk-apla")]
    documents.sort(key=ranker.key)
    assert [document["_id"] for document in documents] == [
        "Marduk-apla",
        "Marduk-zakir",
    ]


def test_collation_is_diacritic_insensitive() -> None:
    ranker = RealiaRelevanceRanker("Marduk")
    assert ranker.key(_document("Mardūk"))[0] == 0


def test_no_match_returns_fallback_rank() -> None:
    ranker = RealiaRelevanceRanker("Marduk")
    assert ranker.key(_document("Enlil", related_terms=("Ellil",)))[0] == NO_MATCH_RANK


def test_richer_entry_wins_within_same_match_tier() -> None:
    ranker = RealiaRelevanceRanker("Marduk")
    sparse = _doc(_id="Marduk-A")
    rich = _doc(
        _id="Marduk-B",
        type=["Divine names"],
        references=[{"id": "x"}, {"id": "y"}],
        reallexikon=[{"id": "1"}],
    )
    documents = [sparse, rich]
    documents.sort(key=ranker.key)
    assert [document["_id"] for document in documents] == ["Marduk-B", "Marduk-A"]


def test_richness_does_not_override_match_tier() -> None:
    ranker = RealiaRelevanceRanker("Marduk")
    exact_sparse = _doc(_id="Marduk")
    substring_rich = _doc(
        _id="Amêl-Marduk",
        type=["Personal names"],
        references=[{"id": "x"}, {"id": "y"}, {"id": "z"}],
    )
    documents = [substring_rich, exact_sparse]
    documents.sort(key=ranker.key)
    assert [document["_id"] for document in documents] == ["Marduk", "Amêl-Marduk"]


def test_reallexikon_counts_as_single_data_point() -> None:
    ranker = RealiaRelevanceRanker("Marduk")
    as_array = ranker.key(_doc(_id="Marduk-A", reallexikon=[{"id": "1"}]))
    as_object = ranker.key(_doc(_id="Marduk-B", reallexikon={"id": "1"}))
    assert as_array[1] == as_object[1] == -1


def test_reallexikon_list_length_does_not_inflate_richness() -> None:
    ranker = RealiaRelevanceRanker("Marduk")
    single = ranker.key(_doc(_id="Marduk-A", reallexikon=[{"id": "1"}]))
    many = ranker.key(
        _doc(_id="Marduk-B", reallexikon=[{"id": "1"}, {"id": "2"}, {"id": "3"}])
    )
    assert single[1] == many[1] == -1


def test_diacritic_tiebreak_is_deterministic() -> None:
    ranker = RealiaRelevanceRanker("Marduk")
    documents = [_document("Mardūk"), _document("Marduk")]
    documents.sort(key=ranker.key)
    assert [document["_id"] for document in documents] == ["Marduk", "Mardūk"]


def test_non_list_related_terms_treated_as_empty() -> None:
    ranker = RealiaRelevanceRanker("Marduk")
    assert ranker.key(_doc(_id="Enlil", relatedTerms="Marduk"))[0] == NO_MATCH_RANK
