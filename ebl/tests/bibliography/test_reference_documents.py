import pytest
from mockito import expect

from ebl.bibliography.application.reference_documents import (
    bibliography_documents_by_lookup,
    hydrate_reference_documents,
)
from ebl.fragmentarium.application.fragment_query_bibliography import (
    bibliography_documents_of,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory
from ebl.tests.fragmentarium.fragment_query_bibliography_test_helpers import (
    reference_of,
    summary_of,
)


def create(repository, id_, **identity):
    entry = BibliographyEntryFactory.build(id=id_, **identity)
    repository.create(entry)
    return entry


@pytest.mark.parametrize("id_", ["OLD", "old", "CITE", "LEGACY"])
def test_lookup_documents_resolve_aliases_and_citation_keys(
    bibliography_repository, id_
):
    entry = create(
        bibliography_repository,
        "CANONICAL",
        citationKey="CITE",
        aliases=[{"value": "OLD", "normalizedValue": "old"}, {"value": "LEGACY"}],
    )

    assert bibliography_documents_by_lookup([id_], bibliography_repository) == {
        id_: entry
    }
    assert bibliography_documents_of(
        [summary_of("X.1", reference_of(id_))], bibliography_repository
    ) == {id_: entry}


def test_lookup_priority_is_canonical_then_citation_key(bibliography_repository):
    canonical = create(bibliography_repository, "ID")
    citation = create(bibliography_repository, "CITATION_OWNER", citationKey="CITE")
    create(
        bibliography_repository,
        "ALIAS_OWNER",
        citationKey="ID",
        aliases=[{"value": "CITE"}],
    )

    assert bibliography_documents_by_lookup(
        ["ID", "CITE"], bibliography_repository
    ) == {
        "ID": canonical,
        "CITE": citation,
    }


@pytest.mark.parametrize("field", ["aliases", "citationKey"])
def test_ambiguous_lookup_is_omitted(bibliography_repository, field):
    identity = [{"value": "SHARED"}] if field == "aliases" else "SHARED"
    for id_ in ("FIRST", "SECOND"):
        create(bibliography_repository, id_, **{field: identity})

    assert bibliography_documents_by_lookup(["SHARED"], bibliography_repository) == {}


def test_alias_on_tombstone_resolves_to_canonical(bibliography_repository):
    canonical = create(bibliography_repository, "CANON")
    create(
        bibliography_repository,
        "OLD",
        aliases=[{"value": "ALIAS"}],
        deprecated=True,
        redirectTo="CANON",
    )

    assert bibliography_documents_by_lookup(["ALIAS"], bibliography_repository) == {
        "ALIAS": canonical
    }


def test_ambiguous_citation_key_does_not_fall_back_to_unique_alias(
    bibliography_repository,
):
    for id_ in ("FIRST", "SECOND"):
        create(bibliography_repository, id_, citationKey="SHARED")
    create(bibliography_repository, "ALIAS", aliases=[{"value": "SHARED"}])

    assert bibliography_documents_by_lookup(["SHARED"], bibliography_repository) == {}


def test_broken_canonical_id_does_not_fall_back_to_alias(bibliography_repository):
    create(bibliography_repository, "BROKEN", deprecated=True, redirectTo="MISSING")
    create(bibliography_repository, "OTHER", aliases=[{"value": "BROKEN"}])

    assert bibliography_documents_by_lookup(["BROKEN"], bibliography_repository) == {}


def test_hydration_uses_batch_lookup_across_all_records(
    bibliography_repository, monkeypatch
):
    canonical = create(bibliography_repository, "CANON", aliases=[{"value": "ALIAS"}])
    calls = []
    query_ids = bibliography_repository.query_by_ids
    query_lookups = bibliography_repository.query_by_lookup_values
    monkeypatch.setattr(
        bibliography_repository,
        "query_by_ids",
        lambda ids: calls.append(("ids", ids)) or query_ids(ids),
    )
    monkeypatch.setattr(
        bibliography_repository,
        "query_by_lookup_values",
        lambda ids: calls.append(("lookups", ids)) or query_lookups(ids),
    )
    records = [
        {"references": [{"id": "ALIAS"}, {"id": "CANON"}]},
        {"references": [{"id": "ALIAS"}, {"id": "UNKNOWN"}]},
    ]

    hydrate_reference_documents(records, bibliography_repository)

    assert calls == [
        ("ids", ["ALIAS", "CANON", "UNKNOWN"]),
        ("lookups", ["ALIAS", "UNKNOWN"]),
    ]
    assert records[0]["references"] == [
        {"id": "ALIAS", "document": canonical},
        {"id": "CANON", "document": canonical},
    ]
    assert records[1]["references"][1] == {"id": "UNKNOWN", "document": None}


def test_empty_hydration_performs_no_repository_calls(bibliography_repository):
    expect(bibliography_repository, times=0).query_by_ids(...)
    expect(bibliography_repository, times=0).query_by_lookup_values(...)

    assert bibliography_documents_by_lookup([], bibliography_repository) == {}
    hydrate_reference_documents([{"references": []}], bibliography_repository)


@pytest.mark.parametrize("aliases", [None, "malformed", {"value": "OTHER"}, ["bad", 7]])
def test_malformed_alias_container_does_not_break_citation_key_hydration(
    bibliography_repository, aliases
):
    canonical = create(
        bibliography_repository, "CANON", citationKey="CITE", aliases=aliases
    )

    assert bibliography_documents_by_lookup(["CITE"], bibliography_repository) == {
        "CITE": canonical
    }


def test_lookup_repository_empty_batch_skips_query(bibliography_repository):
    expect(bibliography_repository._collection, times=0).find_many(...)

    assert bibliography_repository.query_by_lookup_values([]) == []
