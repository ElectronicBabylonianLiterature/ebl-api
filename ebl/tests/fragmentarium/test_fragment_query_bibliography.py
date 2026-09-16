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
