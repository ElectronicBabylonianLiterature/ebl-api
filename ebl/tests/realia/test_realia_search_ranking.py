from ebl.realia.infrastructure.realia_search_ranking import (
    NO_MATCH_RANK,
    RealiaRelevanceRanker,
)


def _document(identifier: str, related_terms=()) -> dict:
    return {"_id": identifier, "relatedTerms": list(related_terms)}


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
