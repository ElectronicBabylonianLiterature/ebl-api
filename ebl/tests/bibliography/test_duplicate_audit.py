from ebl.bibliography.application.duplicate_audit import (
    UsageCounts,
    cluster_pairs,
    generate_candidate_pairs,
    metadata_completeness,
    normalize_doi,
    normalize_entry,
    normalize_isbn,
    normalize_issn,
    normalize_text,
    reviewed_not_duplicate_pairs,
    score_pair,
    suggest_canonical,
)


def entry(id_, **overrides):
    data = {
        "_id": id_,
        "type": "book",
        "title": "The Gilgamesh Epic",
        "author": [{"family": "George", "given": "Andrew"}],
        "issued": {"date-parts": [[2003]]},
        "publisher": "Oxford University Press",
    }
    data.update(overrides)
    return data


def test_normalize_doi() -> None:
    assert normalize_doi(" DOI: https://doi.org/10.123/ABC ") == "10.123/abc"
    assert normalize_doi("http://dx.doi.org/10.1000/X") == "10.1000/x"


def test_normalize_isbn() -> None:
    assert normalize_isbn("978-0-19-927841-1") == "9780199278411"
    assert normalize_isbn("0 306 40615 X") == "030640615X"


def test_normalize_issn() -> None:
    assert normalize_issn("1234-567X") == "1234567X"


def test_normalize_title() -> None:
    assert normalize_text("L'épopée   de Gilgameš!") == "l epopee de gilgames"


def test_contributor_and_year_normalization() -> None:
    normalized = normalize_entry(entry("A"))
    assert normalized.contributors == ("george|a",)
    assert normalized.primary_family == "george"
    assert normalized.year == 2003


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


def test_exact_isbn_duplicate_is_likely_with_compatible_title() -> None:
    left = normalize_entry(entry("A", ISBN="978-0-19-927841-1"))
    right = normalize_entry(
        entry("B", title="The Gilgamesh Epic.", ISBN="9780199278411")
    )
    score = score_pair(left, right)
    assert score.decision == "likely_duplicate"
    assert score.matched_signals["isbn"] == 1.0


def test_issn_only_is_supporting_not_hard_duplicate() -> None:
    left = normalize_entry(
        entry(
            "A",
            type="article-journal",
            title="First Article",
            issued={"date-parts": [[2001]]},
            ISSN="1234-5678",
        )
    )
    right = normalize_entry(
        entry(
            "B",
            type="article-journal",
            title="Different Article",
            issued={"date-parts": [[2010]]},
            ISSN="12345678",
        )
    )
    score = score_pair(left, right)
    assert score.decision != "likely_duplicate"
    assert score.score < 0.76
    assert score.matched_signals["issn"] == 1.0


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


def test_generate_candidate_pairs_honors_false_positive_override() -> None:
    entries = [
        normalize_entry(entry("A", DOI="10.1/a")),
        normalize_entry(entry("B", DOI="10.1/a")),
    ]
    pairs = generate_candidate_pairs(entries, {("A", "B")})
    assert pairs[0].previously_reviewed_not_duplicate is True
    assert pairs[0].decision == "not_duplicate"


def test_duplicate_group_clustering_connects_transitive_pairs() -> None:
    normalized_entries = {
        id_: normalize_entry(entry(id_, title=title))
        for id_, title in {
            "A": "The Gilgamesh Epic",
            "B": "The Gilgamesh Epic Introduction",
            "C": "Gilgamesh Epic Introduction",
        }.items()
    }
    pairs = [
        score_pair(normalized_entries["A"], normalized_entries["B"]),
        score_pair(normalized_entries["B"], normalized_entries["C"]),
    ]
    groups = cluster_pairs(pairs, normalized_entries)
    assert len(groups) == 1
    assert groups[0].member_ids == ["A", "B", "C"]


def test_suggest_canonical_prefers_complete_used_identifier_record() -> None:
    sparse = normalize_entry(entry("A", title="", author=[], DOI=""))
    complete = normalize_entry(entry("B", DOI="10.1/b"))
    canonical_id, reason = suggest_canonical(
        [sparse, complete], {"B": UsageCounts(fragments=3)}
    )
    assert canonical_id == "B"
    assert "usage count (3)" in reason
    assert metadata_completeness(complete) > metadata_completeness(sparse)


def test_reviewed_not_duplicate_pairs(tmp_path) -> None:
    path = tmp_path / "overrides.json"
    path.write_text(
        '{"notDuplicatePairs":[{"leftId":"B","rightId":"A","reason":"Different volume"}]}',
        encoding="utf-8",
    )
    assert reviewed_not_duplicate_pairs(path) == {("A", "B")}
