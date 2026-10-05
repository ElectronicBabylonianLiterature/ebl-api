import falcon
import pytest
from mockito import expect

from ebl.tests.factories.bibliography import BibliographyEntryFactory


@pytest.fixture
def identity_search_entry(bibliography, user):
    entry = BibliographyEntryFactory.build(
        id="UBHD-1718224",
        citationKey="rawlinson1871",
        aliases=[{"value": "RN1971axx", "normalizedValue": "rn1971axx"}],
    )
    bibliography.create(entry, user)
    return entry


@pytest.mark.parametrize(
    "query",
    ["UBHD-1718224", "RN1971axx", "rn1971axx", "rawlinson1871", "  RN1971axx  "],
)
def test_identifier_search_returns_canonical_entry(
    bibliography, client, identity_search_entry, query
):
    assert bibliography.search(query) == [identity_search_entry]

    result = client.simulate_get("/bibliography", params={"query": query})

    assert result.status == falcon.HTTP_OK
    assert result.json == [identity_search_entry]


def test_identifier_search_accepts_legacy_alias_without_normalized_value(
    bibliography, client, database
):
    database["bibliography"].insert_one(
        {"_id": "CANONICAL", "type": "book", "aliases": [{"value": "LS276"}]}
    )
    expected = {"id": "CANONICAL", "type": "book", "aliases": [{"value": "LS276"}]}

    assert bibliography.search("LS276") == [expected]
    result = client.simulate_get("/bibliography", params={"query": "LS276"})
    assert result.status == falcon.HTTP_OK
    assert result.json == [expected]


def test_identifier_search_follows_tombstone(
    bibliography, client, identity_search_entry, user
):
    tombstone = BibliographyEntryFactory.build(
        id="LS276", deprecated=True, redirectTo=identity_search_entry["id"]
    )
    bibliography.create(tombstone, user)

    assert bibliography.search("LS276") == [identity_search_entry]
    result = client.simulate_get("/bibliography", params={"query": "LS276"})
    assert result.status == falcon.HTTP_OK
    assert result.json == [identity_search_entry]


def test_identifier_search_keeps_metadata_matches_and_deduplicates_by_id(
    bibliography, identity_search_entry, bibliography_repository, when
):
    projected_entry = {**identity_search_entry, "title": "Metadata projection"}
    other = BibliographyEntryFactory.build(id="OTHER", title="Additional match")
    (
        when(bibliography_repository)
        .query_by_container_title_and_collection_number("RN1971axx", None)
        .thenReturn([projected_entry, other])
    )

    assert bibliography.search("RN1971axx") == [identity_search_entry, other]


def test_unknown_identifier_keeps_metadata_search(bibliography, client, user):
    entry = BibliographyEntryFactory.build(id="OTHER", title_short="Unresolved")
    bibliography.create(entry, user)

    assert bibliography.search("Unresolved") == [entry]
    result = client.simulate_get("/bibliography", params={"query": "Unresolved"})
    assert result.status == falcon.HTTP_OK
    assert result.json == [entry]


def test_metadata_search_excludes_deprecated_entries(
    bibliography, client, identity_search_entry, user
):
    tombstone = BibliographyEntryFactory.build(
        id="OLD", deprecated=True, redirectTo=identity_search_entry["id"]
    )
    bibliography.create(tombstone, user)

    result = client.simulate_get("/bibliography", params={"query": "Miccadei"})

    assert result.status == falcon.HTTP_OK
    assert result.json == [identity_search_entry]


@pytest.mark.parametrize("field", ["aliases", "citationKey"])
def test_ambiguous_identifier_falls_back_to_metadata_search(
    bibliography_repository, client, database, field, when
):
    identity = (
        [{"value": "shared-key", "normalizedValue": "shared-key"}]
        if field == "aliases"
        else "shared-key"
    )
    for id_ in ("FIRST", "SECOND"):
        database["bibliography"].insert_one(
            {"_id": id_, "type": "book", field: identity}
        )

    other = BibliographyEntryFactory.build(id="OTHER", title="Metadata match")
    (
        when(bibliography_repository)
        .query_by_author_year_and_title("shared-key", None, None)
        .thenReturn([])
    )
    (
        when(bibliography_repository)
        .query_by_container_title_and_collection_number("shared-key", None)
        .thenReturn([other])
    )

    result = client.simulate_get("/bibliography", params={"query": "shared-key"})
    assert result.status == falcon.HTTP_OK
    assert result.json == [other]


@pytest.mark.parametrize("redirect_to", [None, "MISSING"])
def test_unresolvable_tombstone_is_not_an_autocomplete_option(
    bibliography, client, database, redirect_to
):
    entry = {"_id": "BROKEN", "type": "book", "deprecated": True}
    if redirect_to:
        entry["redirectTo"] = redirect_to
    database["bibliography"].insert_one(entry)

    assert bibliography.search("BROKEN") == []
    result = client.simulate_get("/bibliography", params={"query": "BROKEN"})
    assert result.status == falcon.HTTP_OK
    assert result.json == []


def test_redirect_loop_search_returns_no_deprecated_entry(
    bibliography, client, database
):
    for id_, target in [("LOOP_A", "LOOP_B"), ("LOOP_B", "LOOP_A")]:
        database["bibliography"].insert_one(
            {"_id": id_, "type": "book", "deprecated": True, "redirectTo": target}
        )

    assert bibliography.search("LOOP_A") == []
    result = client.simulate_get("/bibliography", params={"query": "LOOP_A"})
    assert result.status == falcon.HTTP_OK
    assert result.json == []


@pytest.mark.parametrize("query", ["", "   "])
def test_blank_query_skips_identifier_lookup(
    bibliography, bibliography_repository, client, query, when
):
    expect(bibliography_repository, times=0).query_by_id(...)
    if query:
        (
            when(bibliography_repository)
            .query_by_author_year_and_title(query, None, None)
            .thenReturn([])
        )

    assert bibliography.search(query) == []
    result = client.simulate_get("/bibliography", params={"query": query})
    assert result.status == falcon.HTTP_OK
    assert result.json == []
