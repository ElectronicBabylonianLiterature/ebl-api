from ebl.bibliography.application.duplicate_audit import (
    UsageCounts,
    collect_usage_counts,
    cluster_pairs,
    member_summary,
    normalize_entry,
    run_audit,
    score_pair,
    suggest_canonical,
    write_reports,
)
from ebl.tests.bibliography.duplicate_audit_test_helpers import entry


class FakeCollection:
    def __init__(
        self,
        documents=(),
        count=0,
        count_error: bool = False,
        find_error: bool = False,
    ):
        self._documents = list(documents)
        self._count = count
        self._count_error = count_error
        self._find_error = find_error

    def count_documents(self, _query):
        if self._count_error:
            raise RuntimeError("count failed")
        return self._count

    def find(self, *_args, **_kwargs):
        if self._find_error:
            raise RuntimeError("find failed")
        return list(self._documents)


def test_run_audit_writes_reports(tmp_path) -> None:
    left = entry("A", DOI="10.1/a")
    right = entry("B", DOI="10.1/a", title="The Gilgamesh Epic.")
    database = {
        "bibliography": FakeCollection([left, right]),
        "fragments": FakeCollection([{"notes": {"text": "@bib{A}"}}], count=1),
        "texts": FakeCollection(count=2),
        "chapters": FakeCollection(count=3),
        "dossiers": FakeCollection(count=4),
    }

    pairs, groups = run_audit(database, tmp_path)

    assert pairs[0].decision == "likely_duplicate"
    assert groups[0].to_dict()["groupMembers"][0]["usageCounts"]["total"] >= 10
    assert (tmp_path / "bibliography_duplicate_candidate_groups.json").exists()
    assert "A,B" in (tmp_path / "bibliography_duplicate_candidate_pairs.csv").read_text(
        encoding="utf-8"
    )
    assert "Top Likely Duplicate Groups" in (
        tmp_path / "bibliography_duplicate_audit_summary.md"
    ).read_text(encoding="utf-8")


def test_write_reports_handles_possible_groups(tmp_path) -> None:
    entries = [
        normalize_entry(entry("A", title="The Gilgamesh Epic")),
        normalize_entry(entry("B", title="The Gilgamesh Epic: Introduction")),
    ]
    pair = score_pair(entries[0], entries[1])
    groups = cluster_pairs([pair], {item.id: item for item in entries})

    write_reports(tmp_path, entries, [pair], groups)

    groups_csv = (tmp_path / "bibliography_duplicate_candidate_groups.csv").read_text(
        encoding="utf-8"
    )
    assert "matchedSignalsSummary" in groups_csv


def test_collect_usage_counts_marks_incomplete_on_failures() -> None:
    database = {
        "fragments": FakeCollection(count_error=True, find_error=True),
        "texts": FakeCollection(),
        "chapters": FakeCollection(),
        "dossiers": FakeCollection(),
    }

    counts = collect_usage_counts(database, ["A"])

    assert counts["A"].fragments == 0
    assert counts["A"].fully_checked is False


def test_suggest_canonical_handles_isbn_and_literal_names() -> None:
    literal = normalize_entry(
        entry(
            "Literal",
            author=[{"literal": "The EBL Project"}],
            DOI="",
            ISBN="9780306406157",
        )
    )
    sparse = normalize_entry(entry("Sparse", title="", author=[], DOI="", ISBN=""))

    canonical_id, reason = suggest_canonical([sparse, literal])

    assert canonical_id == "Literal"
    assert "ISBN" in reason
    assert member_summary(literal, UsageCounts())["authorEditorSummary"] == (
        "The EBL Project"
    )
