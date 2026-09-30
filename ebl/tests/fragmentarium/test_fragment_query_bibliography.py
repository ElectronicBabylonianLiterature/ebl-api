import pytest

from ebl.bibliography.domain.reference import ReferenceType
from ebl.fragmentarium.application.fragment_query_bibliography import (
    bibliography_documents_of,
    bibliography_ids_of,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory
from ebl.tests.fragmentarium.fragment_query_bibliography_test_helpers import (
    reference_of,
    summary_of,
)


def create_entries(bibliography_repository, *ids) -> None:
    for id_ in ids:
        bibliography_repository.create(BibliographyEntryFactory.build(id=id_))


def test_bibliography_ids_are_deduplicated_in_first_seen_order():
    items = [
        summary_of("X.1", reference_of("RN52"), reference_of("RN54")),
        summary_of("X.2", reference_of("RN52", ReferenceType.EDITION)),
    ]

    assert bibliography_ids_of(items) == ["RN52", "RN54"]


def test_repeated_reference_in_one_fragment_is_deduplicated():
    items = [summary_of("X.1", reference_of("RN52"), reference_of("RN52"))]

    assert bibliography_ids_of(items) == ["RN52"]


def test_no_references_skips_the_lookup(spied_bibliography_repository):
    repository, calls = spied_bibliography_repository

    assert bibliography_documents_of([summary_of("X.1")], repository) == {}
    assert calls == []


def test_empty_page_skips_the_lookup(spied_bibliography_repository):
    repository, calls = spied_bibliography_repository

    assert bibliography_documents_of([], repository) == {}
    assert calls == []


def test_single_reference_is_resolved(spied_bibliography_repository):
    repository, calls = spied_bibliography_repository
    create_entries(repository, "RN52")

    documents = bibliography_documents_of(
        [summary_of("X.1", reference_of("RN52"))], repository
    )

    assert set(documents) == {"RN52"}
    assert documents["RN52"]["id"] == "RN52"
    assert calls == [["RN52"]]


def test_many_occurrences_resolve_in_one_batch(spied_bibliography_repository):
    repository, calls = spied_bibliography_repository
    ids = [f"RN{index}" for index in range(8)]
    create_entries(repository, *ids)
    items = [
        summary_of(
            f"X.{fragment_index}",
            *(
                reference_of(ids[(fragment_index * 4 + occurrence) % 8])
                for occurrence in range(4)
            ),
        )
        for fragment_index in range(8)
    ]

    documents = bibliography_documents_of(items, repository)

    assert sum(len(item.references) for item in items) == 32
    assert set(documents) == set(ids)
    assert calls == [ids]


def test_missing_document_is_absent(spied_bibliography_repository):
    repository, calls = spied_bibliography_repository
    create_entries(repository, "RN52")

    documents = bibliography_documents_of(
        [summary_of("X.1", reference_of("RN52"), reference_of("RN99"))], repository
    )

    assert set(documents) == {"RN52"}
    assert calls == [["RN52", "RN99"]]


@pytest.mark.parametrize(
    "entry",
    [
        {"id": "RN52", "type": "book", "DOI": "10.1000/1"},
        {"id": "RN52", "type": "book", "URL": "https://example.com"},
        {"id": "RN52", "type": "book"},
    ],
)
def test_documents_are_returned_as_stored(spied_bibliography_repository, entry):
    repository, _ = spied_bibliography_repository
    repository.create(entry)

    documents = bibliography_documents_of(
        [summary_of("X.1", reference_of("RN52"))], repository
    )

    assert documents == {"RN52": entry}


@pytest.mark.parametrize("cycle_length", [1, 2, 5])
def test_redirect_cycles_are_omitted(spied_bibliography_repository, cycle_length):
    repository, calls = spied_bibliography_repository
    ids = [f"CYCLE{index}" for index in range(cycle_length)]
    for index, id_ in enumerate(ids):
        repository.create(
            BibliographyEntryFactory.build(
                id=id_, deprecated=True, redirectTo=ids[(index + 1) % cycle_length]
            )
        )

    documents = bibliography_documents_of(
        [summary_of("X.1", reference_of(ids[0]))], repository
    )

    assert documents == {}
    assert calls == [[id_] for id_ in ids]


@pytest.mark.parametrize("redirect_to", [None, "", 42])
def test_deprecated_document_without_usable_target_is_omitted(
    spied_bibliography_repository, redirect_to
):
    repository, calls = spied_bibliography_repository
    entry = BibliographyEntryFactory.build(id="OLD", deprecated=True)
    if redirect_to is not None:
        entry["redirectTo"] = redirect_to
    repository.create(entry)

    documents = bibliography_documents_of(
        [summary_of("X.1", reference_of("OLD"))], repository
    )

    assert documents == {}
    assert calls == [["OLD"]]


def test_late_dangling_redirect_is_omitted(spied_bibliography_repository):
    repository, calls = spied_bibliography_repository
    ids = [f"LATE{index}" for index in range(5)]
    for index, current in enumerate(ids):
        target = ids[index + 1] if index + 1 < len(ids) else "MISSING"
        repository.create(
            BibliographyEntryFactory.build(
                id=current, deprecated=True, redirectTo=target
            )
        )

    documents = bibliography_documents_of(
        [summary_of("X.1", reference_of(ids[0]))], repository
    )

    assert documents == {}
    assert calls == [[id_] for id_ in [*ids, "MISSING"]]


def test_confirmed_missing_id_is_not_queried_as_a_redirect_target(
    spied_bibliography_repository,
):
    repository, calls = spied_bibliography_repository
    repository.create(
        BibliographyEntryFactory.build(id="OLD", deprecated=True, redirectTo="MISSING")
    )

    documents = bibliography_documents_of(
        [summary_of("X.1", reference_of("MISSING"), reference_of("OLD"))],
        repository,
    )

    assert documents == {}
    assert calls == [["MISSING", "OLD"]]


def test_repository_failures_propagate(monkeypatch, bibliography_repository):
    def fail_query(ids):
        raise RuntimeError("bibliography unavailable")

    monkeypatch.setattr(bibliography_repository, "query_by_ids", fail_query)

    with pytest.raises(RuntimeError, match="bibliography unavailable"):
        bibliography_documents_of(
            [summary_of("X.1", reference_of("RN52"))], bibliography_repository
        )
