import pytest
from mockito import expect

from ebl.bibliography.application.reference_search import (
    equivalent_reference_identities,
)
from ebl.bibliography.application.reference_search_identities import (
    ReferenceSearchIdentities,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory


@pytest.fixture
def lookup_calls(bibliography_repository, monkeypatch):
    calls = []
    for name in (
        "query_by_id",
        "query_by_ids",
        "query_by_lookup_values",
        "query_by_redirect_targets",
    ):
        original = getattr(bibliography_repository, name)

        def recording(*args, _name=name, _original=original, **kwargs):
            calls.append((_name, args, kwargs))
            return _original(*args, **kwargs)

        monkeypatch.setattr(bibliography_repository, name, recording)
    return calls


def test_one_thousand_lookup_identities_use_four_queries(
    bibliography_repository, lookup_calls
):
    aliases = [f"alias{index:04}" for index in range(999)]
    bibliography_repository.create(
        BibliographyEntryFactory.build(
            id="CANON",
            aliases=[{"value": value, "normalizedValue": value} for value in aliases],
        )
    )

    assert equivalent_reference_identities(
        "CANON", bibliography_repository
    ) == ReferenceSearchIdentities(
        bibliography_ids=("CANON",),
        alias_values=tuple(aliases),
        normalized_alias_values=tuple(aliases),
    )
    assert [call[0] for call in lookup_calls] == [
        "query_by_id",
        "query_by_redirect_targets",
        "query_by_ids",
        "query_by_lookup_values",
    ]


def test_wide_reverse_frontier_uses_one_query_per_depth(
    bibliography_repository, lookup_calls
):
    predecessor_ids = [f"OLD{index:04}" for index in range(999)]
    bibliography_repository.create(BibliographyEntryFactory.build(id="CANON"))
    for id_ in predecessor_ids:
        bibliography_repository.create(
            BibliographyEntryFactory.build(id=id_, deprecated=True, redirectTo="CANON")
        )

    identities = equivalent_reference_identities("CANON", bibliography_repository)
    assert identities.bibliography_ids[0] == "CANON"
    assert sorted(identities.bibliography_ids[1:]) == predecessor_ids
    assert identities.stored_reference_values() == identities.bibliography_ids
    reverse_calls = [
        call for call in lookup_calls if call[0] == "query_by_redirect_targets"
    ]
    assert len(reverse_calls) == 2
    assert reverse_calls[0][1] == (["CANON"],)
    assert set(reverse_calls[1][1][0]) == set(predecessor_ids)
    assert [call[0] for call in lookup_calls] == [
        "query_by_id",
        "query_by_redirect_targets",
        "query_by_redirect_targets",
        "query_by_ids",
    ]


def test_batched_secondary_id_validation_keeps_lookup_precedence(
    bibliography_repository,
):
    for entry in (
        BibliographyEntryFactory.build(
            id="CANON",
            aliases=[{"value": "SHARED"}, {"value": "COLLIDING_ID"}],
            citationKey="COLLIDING_KEY",
        ),
        BibliographyEntryFactory.build(id="COLLIDING_ID"),
        BibliographyEntryFactory.build(id="OTHER", citationKey="COLLIDING_KEY"),
        BibliographyEntryFactory.build(id="ALIAS_OWNER", aliases=[{"value": "SHARED"}]),
    ):
        bibliography_repository.create(entry)

    assert equivalent_reference_identities(
        "CANON", bibliography_repository
    ) == ReferenceSearchIdentities(bibliography_ids=("CANON",))


def test_empty_reverse_targets_skip_database_lookup(bibliography_repository):
    expect(bibliography_repository._collection, times=0).find_many(...)

    assert bibliography_repository.query_by_redirect_targets([], limit=10) == []
