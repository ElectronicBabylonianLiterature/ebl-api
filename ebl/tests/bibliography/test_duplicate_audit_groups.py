from ebl.bibliography.application.duplicate_audit import (
    UsageCounts,
    cluster_pairs,
    generate_candidate_pairs,
    metadata_completeness,
    normalize_entry,
    reviewed_not_duplicate_pairs,
    score_pair,
    suggest_canonical,
)
from ebl.tests.bibliography.duplicate_audit_test_helpers import entry


def test_mixed_candidate_group_does_not_pull_weak_related_record_into_likely_group() -> (
    None
):
    normalized_entries = {
        id_: normalize_entry(data)
        for id_, data in {
            "A": entry(
                "A",
                title="The Marduk Prophecy",
                author=[{"family": "Lambert", "given": "Wilfred"}],
                issued={"date-parts": [[1998]]},
                page="1-20",
                **{"container-title": "Journal of Ancient Near Eastern Studies"},
            ),
            "B": entry(
                "B",
                title="The Marduk Prophecy.",
                author=[{"family": "Lambert", "given": "Wilfred"}],
                issued={"date-parts": [[1998]]},
                page="1-20",
                **{"container-title": "Journal of Ancient Near Eastern Studies"},
            ),
            "C": entry(
                "C",
                title="Notes on Marduk Theology",
                author=[{"family": "Lambert", "given": "Wilfred"}],
                issued={"date-parts": [[1998]]},
                page="21-42",
                **{"container-title": "Journal of Ancient Near Eastern Studies"},
            ),
        }.items()
    }
    pairs = [
        score_pair(normalized_entries["A"], normalized_entries["B"]),
        score_pair(normalized_entries["A"], normalized_entries["C"]),
    ]
    groups = cluster_pairs(pairs, normalized_entries)

    likely_groups = [
        group for group in groups if group.group_decision == "likely_duplicate"
    ]
    assert likely_groups[0].member_ids == ["A", "B"]


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


def test_mixed_candidate_group_splits_unrelated_record() -> None:
    normalized_entries = {
        id_: normalize_entry(data)
        for id_, data in {
            "Steinkeller1989Sale": entry(
                "Steinkeller1989Sale",
                type="book",
                title="Sale Documents of the Ur-III-Period",
                author=[{"family": "Steinkeller", "given": "Piotr"}],
                issued={"date-parts": [[1989]]},
                publisher="Franz Steiner",
                **{"collection-title": "FAOS", "collection-number": "17"},
            ),
            "FAOS_17": entry(
                "FAOS_17",
                type="book",
                title="Sale Documents of the Ur-III-Period",
                author=[{"family": "Steinkeller", "given": "Piotr"}],
                issued={"date-parts": [[1989]]},
                publisher="Franz Steiner",
                **{"collection-title": "FAOS"},
            ),
            "NABU1989-21": entry(
                "NABU1989-21",
                type="article-journal",
                title="Piotr Steinkeller",
                author=[{"family": "Steinkeller", "given": "Piotr"}],
                issued={"date-parts": [[1989]]},
                **{"container-title": "NABU", "volume": "1989"},
            ),
        }.items()
    }
    pairs = [
        score_pair(
            normalized_entries["Steinkeller1989Sale"], normalized_entries["FAOS_17"]
        ),
        score_pair(
            normalized_entries["Steinkeller1989Sale"], normalized_entries["NABU1989-21"]
        ),
    ]
    groups = cluster_pairs(pairs, normalized_entries)

    likely_groups = [
        group for group in groups if group.group_decision == "likely_duplicate"
    ]
    assert len(likely_groups) == 1
    assert set(likely_groups[0].member_ids) == {"Steinkeller1989Sale", "FAOS_17"}


def test_reviewed_not_duplicate_pairs(tmp_path) -> None:
    path = tmp_path / "overrides.json"
    path.write_text(
        '{"notDuplicatePairs":[{"leftId":"B","rightId":"A","reason":"Different volume"}]}',
        encoding="utf-8",
    )
    assert reviewed_not_duplicate_pairs(path) == {("A", "B")}
