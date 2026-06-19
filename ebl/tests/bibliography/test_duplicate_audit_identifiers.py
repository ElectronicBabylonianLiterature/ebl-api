from ebl.bibliography.application.duplicate_audit import normalize_entry, score_pair
from ebl.tests.bibliography.duplicate_audit_test_helpers import (
    entry,
    score_entries,
)


def test_exact_doi_duplicate_is_likely() -> None:
    left = normalize_entry(entry("A", DOI="10.123/ABC"))
    right = normalize_entry(entry("B", DOI="https://doi.org/10.123/abc"))
    score = score_pair(left, right)
    assert score.decision == "likely_duplicate"
    assert score.score >= 0.97
    assert score.matched_signals["doi"] == 1.0


def test_exact_doi_with_conflict_still_needs_review() -> None:
    left = normalize_entry(entry("A", DOI="10.123/ABC"))
    right = normalize_entry(
        entry("B", DOI="10.123/abc", issued={"date-parts": [[1999]]})
    )
    score = score_pair(left, right)
    assert score.decision == "possible_duplicate"
    assert score.score >= 0.76
    assert score.matched_signals["doi"] == 1.0
    assert "year" in score.conflicting_signals


def test_exact_doi_with_strong_metadata_conflict_flags_data_issue() -> None:
    left = normalize_entry(
        entry(
            "A",
            type="article-journal",
            title="On Gilgamesh",
            author=[{"family": "George", "given": "Andrew"}],
            issued={"date-parts": [[2003]]},
            DOI="10.123/abc",
            page="1-10",
        )
    )
    right = normalize_entry(
        entry(
            "B",
            type="article-journal",
            title="A Study of Astronomical Diaries",
            author=[{"family": "Rochberg", "given": "Francesca"}],
            issued={"date-parts": [[1991]]},
            DOI="10.123/abc",
            page="44-60",
        )
    )
    score = score_pair(left, right)
    assert score.decision == "possible_duplicate"
    assert score.matched_signals["doi"] == 1.0
    assert "doi_data_issue" in score.conflicting_signals


def test_exact_isbn_duplicate_is_likely_with_compatible_title() -> None:
    left = normalize_entry(entry("A", ISBN="978-0-19-927841-1"))
    right = normalize_entry(
        entry("B", title="The Gilgamesh Epic.", ISBN="9780199278411")
    )
    score = score_pair(left, right)
    assert score.decision == "likely_duplicate"
    assert score.matched_signals["isbn"] == 1.0


def test_exact_isbn_duplicate_is_likely_with_compatible_volume() -> None:
    left = normalize_entry(
        entry(
            "A", title="Royal Inscriptions Volume 1", volume="1", ISBN="9780199278411"
        )
    )
    right = normalize_entry(
        entry(
            "B",
            title="Royal Inscriptions Volume I",
            volume="1",
            ISBN="978-0-19-927841-1",
        )
    )
    score = score_pair(left, right)
    assert score.decision == "likely_duplicate"
    assert score.matched_signals["isbn"] == 1.0


def test_exact_doi_with_low_title_and_contributor_similarity_is_downgraded() -> None:
    left = normalize_entry(
        entry(
            "A",
            title="Administrative Documents from Nippur",
            author=[{"family": "Jones", "given": "Mary"}],
            issued={"date-parts": [[1971]]},
            DOI="10.5555/copied",
            page="1-50",
        )
    )
    right = normalize_entry(
        entry(
            "B",
            title="A Grammar of Old Babylonian Letters",
            author=[{"family": "Black", "given": "Jeremy"}],
            issued={"date-parts": [[2001]]},
            DOI="10.5555/copied",
            page="100-160",
        )
    )
    score = score_pair(left, right)
    assert score.decision == "possible_duplicate"
    assert score.matched_signals["doi"] == 1.0
    assert "doi_data_issue" in score.conflicting_signals
    assert "different_title" in score.conflicting_signals


def test_issn_only_is_supporting_not_hard_duplicate() -> None:
    score = score_entries(
        {
            "type": "article-journal",
            "title": "First Article",
            "issued": {"date-parts": [[2001]]},
            "ISSN": "1234-5678",
        },
        {
            "type": "article-journal",
            "title": "Different Article",
            "issued": {"date-parts": [[2010]]},
            "ISSN": "12345678",
        },
    )
    assert score.decision != "likely_duplicate"
    assert score.score < 0.76
    assert score.matched_signals["issn"] == 1.0


def test_doi_title_conflict_is_not_likely_duplicate() -> None:
    left = normalize_entry(
        entry(
            "A",
            type="book",
            title="Sumerian Grammatical Texts",
            DOI="10.123/SharedDoi",
            **{
                "collection-title": "PBS",
                "container-title": "PBS",
                "publisher": "University Museum",
            },
        )
    )
    right = normalize_entry(
        entry(
            "B",
            type="book",
            title="Sumerian Liturgical Texts",
            DOI="10.123/SharedDoi",
            **{
                "collection-title": "PBS",
                "container-title": "PBS",
                "publisher": "University Museum",
            },
        )
    )
    score = score_pair(left, right)
    assert score.decision != "likely_duplicate"
    assert score.matched_signals["doi"] == 1.0
    assert "doi_data_issue" in score.conflicting_signals
