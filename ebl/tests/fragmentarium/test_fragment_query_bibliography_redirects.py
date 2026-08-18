from ebl.bibliography.application.bibliography import MAX_REDIRECT_DEPTH
from ebl.fragmentarium.application.fragment_query_bibliography import (
    bibliography_documents_of,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory
from ebl.tests.fragmentarium.fragment_query_bibliography_test_helpers import (
    reference_of,
    summary_of,
)


def create_entry(repository, id_: str, redirect_to=None) -> dict:
    entry = BibliographyEntryFactory.build(
        id=id_,
        **({"deprecated": True, "redirectTo": redirect_to} if redirect_to else {}),
    )
    repository.create(entry)
    return entry


def create_chain(repository, ids) -> dict:
    for index, current in enumerate(ids[:-1]):
        create_entry(repository, current, redirect_to=ids[index + 1])
    return create_entry(repository, ids[-1])


def test_active_reference_uses_one_batch(spied_bibliography_repository):
    repository, calls = spied_bibliography_repository
    active = create_entry(repository, "ACTIVE2")

    documents = bibliography_documents_of(
        [summary_of("X.1", reference_of("ACTIVE2"))], repository
    )

    assert documents == {"ACTIVE2": active}
    assert calls == [["ACTIVE2"]]


def test_deprecated_reference_resolves_under_original_key(
    spied_bibliography_repository,
):
    repository, calls = spied_bibliography_repository
    create_entry(repository, "OLD1", redirect_to="CANON1")
    canonical = create_entry(repository, "CANON1")

    documents = bibliography_documents_of(
        [summary_of("X.1", reference_of("OLD1"))], repository
    )

    assert set(documents) == {"OLD1"}
    assert documents["OLD1"] == canonical
    assert documents["OLD1"]["id"] == "CANON1"
    assert calls == [["OLD1"], ["CANON1"]]


def test_shared_redirect_target_is_queried_once(spied_bibliography_repository):
    repository, calls = spied_bibliography_repository
    for id_ in ("OLD1", "OLD2", "OLD3"):
        create_entry(repository, id_, redirect_to="CANON")
    canonical = create_entry(repository, "CANON")

    documents = bibliography_documents_of(
        [
            summary_of("X.1", reference_of("OLD1"), reference_of("OLD2")),
            summary_of("X.2", reference_of("OLD3")),
        ],
        repository,
    )

    assert documents == {"OLD1": canonical, "OLD2": canonical, "OLD3": canonical}
    assert calls == [["OLD1", "OLD2", "OLD3"], ["CANON"]]


def test_mixed_active_and_deprecated(spied_bibliography_repository):
    repository, calls = spied_bibliography_repository
    create_entry(repository, "OLD1", redirect_to="CANON1")
    canonical = create_entry(repository, "CANON1")
    active = create_entry(repository, "ACTIVE2")

    documents = bibliography_documents_of(
        [summary_of("X.1", reference_of("OLD1"), reference_of("ACTIVE2"))], repository
    )

    assert documents == {"OLD1": canonical, "ACTIVE2": active}
    assert calls == [["OLD1", "ACTIVE2"], ["CANON1"]]


def test_missing_requested_id_is_omitted(spied_bibliography_repository):
    repository, calls = spied_bibliography_repository
    active = create_entry(repository, "ACTIVE2")

    documents = bibliography_documents_of(
        [summary_of("X.1", reference_of("ACTIVE2"), reference_of("GONE"))], repository
    )

    assert documents == {"ACTIVE2": active}
    assert calls == [["ACTIVE2", "GONE"]]


def test_dangling_redirect_keeps_the_stored_record(spied_bibliography_repository):
    repository, calls = spied_bibliography_repository
    deprecated = create_entry(repository, "OLD1", redirect_to="DOES_NOT_EXIST")

    documents = bibliography_documents_of(
        [summary_of("X.1", reference_of("OLD1"))], repository
    )

    assert documents == {"OLD1": deprecated}
    assert calls == [["OLD1"], ["DOES_NOT_EXIST"]]


def test_no_references_performs_no_lookup(spied_bibliography_repository):
    repository, calls = spied_bibliography_repository

    assert bibliography_documents_of([summary_of("X.1")], repository) == {}
    assert calls == []


def test_chained_redirect_resolves_to_the_terminal_record(
    spied_bibliography_repository,
):
    repository, calls = spied_bibliography_repository
    canonical = create_chain(repository, ["OLD", "MID", "CANON"])

    documents = bibliography_documents_of(
        [summary_of("X.1", reference_of("OLD"))], repository
    )

    assert documents == {"OLD": canonical}
    assert documents["OLD"]["id"] == "CANON"
    assert calls == [["OLD"], ["MID"], ["CANON"]]


def test_chained_redirects_share_one_batch_per_hop(spied_bibliography_repository):
    repository, calls = spied_bibliography_repository
    canonical = create_chain(repository, ["OLD1", "MID", "CANON"])
    create_entry(repository, "OLD2", redirect_to="MID")

    documents = bibliography_documents_of(
        [summary_of("X.1", reference_of("OLD1"), reference_of("OLD2"))], repository
    )

    assert documents == {"OLD1": canonical, "OLD2": canonical}
    assert calls == [["OLD1", "OLD2"], ["MID"], ["CANON"]]


def test_chain_longer_than_the_redirect_depth_stops_safely(
    spied_bibliography_repository,
):
    repository, calls = spied_bibliography_repository
    ids = [f"HOP{index}" for index in range(MAX_REDIRECT_DEPTH + 3)]
    create_chain(repository, ids)

    documents = bibliography_documents_of(
        [summary_of("X.1", reference_of(ids[0]))], repository
    )

    assert len(calls) == MAX_REDIRECT_DEPTH + 1
    assert documents[ids[0]]["id"] == ids[MAX_REDIRECT_DEPTH]
    assert set(documents) == {ids[0]}


def test_redirect_cycle_terminates_without_extra_queries(
    spied_bibliography_repository,
):
    repository, calls = spied_bibliography_repository
    create_entry(repository, "A", redirect_to="B")
    create_entry(repository, "B", redirect_to="A")

    documents = bibliography_documents_of(
        [summary_of("X.1", reference_of("A"))], repository
    )

    assert calls == [["A"], ["B"]]
    assert set(documents) == {"A"}


def test_many_occurrences_use_two_batches(spied_bibliography_repository):
    repository, calls = spied_bibliography_repository
    requested = [f"RN{index}" for index in range(8)]
    redirects = {"RN0": "CANON_A", "RN1": "CANON_A", "RN2": "CANON_B"}
    for id_ in requested:
        create_entry(repository, id_, redirect_to=redirects.get(id_))
    for id_ in ("CANON_A", "CANON_B"):
        create_entry(repository, id_)

    items = [
        summary_of(
            f"X.{fragment_index}",
            *(
                reference_of(requested[(fragment_index * 4 + occurrence) % 8])
                for occurrence in range(4)
            ),
        )
        for fragment_index in range(8)
    ]
    documents = bibliography_documents_of(items, repository)

    assert sum(len(item.references) for item in items) == 32
    assert calls == [requested, ["CANON_A", "CANON_B"]]
    assert set(documents) == set(requested)
    assert documents["RN0"]["id"] == "CANON_A"
    assert documents["RN1"]["id"] == "CANON_A"
    assert documents["RN2"]["id"] == "CANON_B"
    assert documents["RN3"]["id"] == "RN3"
