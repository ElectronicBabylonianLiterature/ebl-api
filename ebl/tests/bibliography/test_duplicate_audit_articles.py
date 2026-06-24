from ebl.bibliography.application.duplicate_audit import normalize_entry, score_pair
from ebl.tests.bibliography.duplicate_audit_test_helpers import (
    entry,
    score_entries,
)


def test_article_siblings_with_different_titles_and_pages_are_not_likely() -> None:
    score = score_entries(
        {
            "type": "article-journal",
            "title": "First Note on Uruk",
            "page": "1-10",
            "container-title": "NABU",
            "volume": "12",
        },
        {
            "type": "article-journal",
            "title": "Second Note on Sippar",
            "page": "11-20",
            "container-title": "NABU",
            "volume": "12",
        },
    )
    assert score.decision != "likely_duplicate"
    assert "different_page" in score.conflicting_signals


def test_chapter_collection_siblings_with_different_titles_and_pages_are_not_likely() -> (
    None
):
    left = normalize_entry(
        entry(
            "A",
            type="chapter",
            title="Trade in Babylonia",
            page="1-18",
            **{"container-title": "Studies in Cuneiform Culture", "publisher": "Brill"},
        )
    )
    right = normalize_entry(
        entry(
            "B",
            type="chapter",
            title="Astronomy in Assyria",
            page="19-38",
            **{"container-title": "Studies in Cuneiform Culture", "publisher": "Brill"},
        )
    )
    score = score_pair(left, right)
    assert score.decision != "likely_duplicate"
    assert "different_page" in score.conflicting_signals


def test_same_author_year_fuzzy_title_is_possible() -> None:
    left = normalize_entry(entry("A", title="The Gilgamesh Epic"))
    right = normalize_entry(entry("B", title="The Gilgamesh Epic: Introduction"))
    score = score_pair(left, right)
    assert score.decision in {"possible_duplicate", "likely_duplicate"}
    contributor_score = score.matched_signals["contributors"]
    assert contributor_score is not None
    assert contributor_score >= 0.9
    assert score.matched_signals["year"] == 1.0


def test_article_container_page_matching_scores() -> None:
    left = normalize_entry(
        entry(
            "A",
            type="article-journal",
            title="A Study of Gilgamesh",
            **{
                "container-title": "Journal of Cuneiform Studies",
                "volume": "12",
                "issue": "1",
                "page": "1-20",
            },
        )
    )
    right = normalize_entry(
        entry(
            "B",
            type="article-journal",
            title="A Study of Gilgameš",
            **{
                "container-title": "Journal of Cuneiform Studies",
                "volume": "12",
                "issue": "1",
                "page": "1–20",
            },
        )
    )
    score = score_pair(left, right)
    assert score.decision == "likely_duplicate"
    assert score.matched_signals["containerTitle"] == 1.0


def test_title_punctuation_diacritic_case_variants_remain_likely() -> None:
    left = normalize_entry(
        entry(
            "A",
            title="L'epopee de Gilgames",
            page="1-20",
            **{"container-title": "Journal of Cuneiform Studies"},
        )
    )
    right = normalize_entry(
        entry(
            "B",
            title="L'épopée de Gilgameš!",
            page="1-20",
            **{"container-title": "Journal of Cuneiform Studies"},
        )
    )
    score = score_pair(left, right)
    assert score.decision == "likely_duplicate"


def test_id_format_variants_with_same_bibliography_remain_likely() -> None:
    left = normalize_entry(
        entry("George.2003", title="The Babylonian Gilgamesh Epic", page="1-20")
    )
    right = normalize_entry(
        entry("George_2003", title="The Babylonian Gilgamesh Epic", page="1-20")
    )
    score = score_pair(left, right)
    assert score.decision == "likely_duplicate"


def test_book_edition_variation_creates_conflict() -> None:
    left = normalize_entry(entry("A", edition="1"))
    right = normalize_entry(entry("B", edition="2"))
    score = score_pair(left, right)
    assert "edition" in score.conflicting_signals


def test_missing_author_year_title_is_insufficient() -> None:
    left = normalize_entry({"_id": "A", "type": "book", "ISSN": "1234-5678"})
    right = normalize_entry({"_id": "B", "type": "book", "ISSN": "12345678"})
    score = score_pair(left, right)
    assert score.decision == "insufficient_data"
