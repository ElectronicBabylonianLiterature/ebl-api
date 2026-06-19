import pytest

from ebl.bibliography.application.duplicate_audit import (
    CandidateGroup,
    PairScore,
    UsageCounts,
    add_note_markup_counts,
    blocking_buckets,
    can_link_candidate_group,
    contributor_similarity,
    is_different_webpage_title,
    is_series_part_sibling,
    jaccard,
    normalize_doi,
    normalize_entry,
    normalize_text,
    parse_series_number,
    primary_initials,
    reviewed_not_duplicate_pairs,
    weighted_match_score,
    year_similarity,
)
from ebl.tests.bibliography.duplicate_audit_test_helpers import entry


def test_reviewed_not_duplicate_pairs_missing_path() -> None:
    assert reviewed_not_duplicate_pairs(None) == set()


def test_normalization_defensive_branches() -> None:
    assert normalize_doi("10.123/white space") == ""
    assert normalize_text("ＡＢＣ", fold_diacritics=False) == "abc"
    assert (
        normalize_entry({"_id": "A", "issued": {"date-parts": [["bad"]]}}).year is None
    )


def test_similarity_defensive_branches() -> None:
    assert jaccard(set(), {"a"}) is None
    assert primary_initials(normalize_entry(entry("A", author=[]))) == ""
    assert year_similarity(2000, 2001) == 0.35
    assert weighted_match_score({"title": None}, {"title": 1.0}) == 0.0
    assert (
        contributor_similarity(
            normalize_entry(entry("A", author=[{"family": "George"}])),
            normalize_entry(entry("B", author=[{"family": "George"}])),
        )
        == 1.0
    )


def test_series_and_webpage_branch_helpers() -> None:
    left = normalize_entry(entry("A", title="Royal Archives"))
    right = normalize_entry(entry("B", title="Royal Archives II"))
    webpage_left = normalize_entry(
        entry("C", type="webpage", title="Record (http://example.com/a)")
    )
    webpage_right = normalize_entry(
        entry("D", type="webpage", title="Record (http://example.com/b)")
    )

    assert is_series_part_sibling(left, right)
    assert is_different_webpage_title(webpage_left, webpage_right, {"title": 1.0})
    assert parse_series_number("iv") == 4
    assert parse_series_number("invalid") is None


@pytest.mark.parametrize("title", ["Royal Archives", "A I"])
def test_short_or_unnumbered_titles_have_no_series_part(title) -> None:
    normalized = normalize_entry(entry("A", title=title))

    assert not is_series_part_sibling(normalized, normalize_entry(entry("B")))


def test_blocking_buckets_include_container_year() -> None:
    buckets = blocking_buckets(
        [
            normalize_entry(
                entry(
                    "A",
                    type="article-journal",
                    **{"container-title": "Journal of Cuneiform Studies"},
                )
            )
        ]
    )

    assert ("container_year", "journal of cuneiform studies", 2003) in buckets


def test_candidate_group_decision_branches() -> None:
    entries = {"A": normalize_entry(entry("A")), "B": normalize_entry(entry("B"))}

    assert candidate_group_with_decision(
        "possible_duplicate", entries
    ).group_decision == ("possible_duplicate")
    assert candidate_group_with_decision(
        "insufficient_data", entries
    ).group_decision == ("insufficient_data")
    assert candidate_group_with_decision("not_duplicate", entries).group_decision == (
        "not_duplicate"
    )


def test_can_link_candidate_group_rejects_conflicts_and_weak_titles() -> None:
    assert not can_link_candidate_group(
        pair_score("possible_duplicate", {"title": 0.9}, ["different_title"])
    )
    assert not can_link_candidate_group(
        pair_score("possible_duplicate", {"title": 0.4}, [])
    )


def test_add_note_markup_counts_ignores_empty_counts() -> None:
    add_note_markup_counts({}, {})


def candidate_group_with_decision(decision: str, entries):
    return CandidateGroup(
        "",
        ["A", "B"],
        [pair_score(decision, {"title": 0.8}, [])],
        "A",
        "",
        {"A": UsageCounts()},
        entries,
    )


def pair_score(decision: str, matched_signals, conflicting_signals):
    return PairScore(
        "A",
        "B",
        0.8,
        decision,
        matched_signals,
        conflicting_signals,
        1.0,
        "",
        "",
    )
