import pytest
from mockito import verify

from ebl.bibliography.application.bibliography import MAX_REDIRECT_DEPTH
from ebl.errors import DuplicateError, NotFoundError
from ebl.tests.factories.bibliography import BibliographyEntryFactory


def test_find(bibliography, bibliography_repository, when):
    bibliography_entry = BibliographyEntryFactory.build()
    (
        when(bibliography_repository)
        .query_by_id(bibliography_entry["id"])
        .thenReturn(bibliography_entry)
    )
    assert bibliography.find(bibliography_entry["id"]) == bibliography_entry


def test_find_redirects_deprecated_id(bibliography, bibliography_repository, when):
    canonical_entry = BibliographyEntryFactory.build(id="CANONICAL_ID")
    deprecated_entry = BibliographyEntryFactory.build(
        id="DUPLICATE_ID", deprecated=True, redirectTo="CANONICAL_ID"
    )
    (
        when(bibliography_repository)
        .query_by_id(deprecated_entry["id"])
        .thenReturn(deprecated_entry)
    )
    (
        when(bibliography_repository)
        .query_by_id(canonical_entry["id"])
        .thenReturn(canonical_entry)
    )

    assert bibliography.find(deprecated_entry["id"]) == canonical_entry


def test_find_many_deduplicates_redirected_canonical_entries(
    bibliography, bibliography_repository, when
):
    canonical_entry = BibliographyEntryFactory.build(id="CANONICAL_ID")
    deprecated_entry = BibliographyEntryFactory.build(
        id="DUPLICATE_ID", deprecated=True, redirectTo=canonical_entry["id"]
    )
    ids = [deprecated_entry["id"], canonical_entry["id"]]
    when(bibliography_repository).query_by_ids(ids).thenReturn(
        [deprecated_entry, canonical_entry]
    )
    (
        when(bibliography_repository)
        .query_by_id(canonical_entry["id"])
        .thenReturn(canonical_entry)
    )

    assert bibliography.find_many(ids) == [canonical_entry]


def test_find_redirects_deprecated_citation_key(
    bibliography, bibliography_repository, when
):
    citation_key = "duplicateCitationKey"
    canonical_entry = BibliographyEntryFactory.build(id="CANONICAL_ID")
    deprecated_entry = BibliographyEntryFactory.build(
        id="DUPLICATE_ID",
        citationKey=citation_key,
        deprecated=True,
        redirectTo=canonical_entry["id"],
    )
    when(bibliography_repository).query_by_id(citation_key).thenRaise(NotFoundError)
    (
        when(bibliography_repository)
        .query_by_citation_key(citation_key)
        .thenReturn(deprecated_entry)
    )
    (
        when(bibliography_repository)
        .query_by_id(canonical_entry["id"])
        .thenReturn(canonical_entry)
    )

    assert bibliography.find(citation_key) == canonical_entry


def test_find_rejects_missing_redirect_target(
    bibliography, bibliography_repository, when
):
    deprecated_entry = BibliographyEntryFactory.build(
        id="DUPLICATE_ID", deprecated=True, redirectTo="MISSING_ID"
    )
    (
        when(bibliography_repository)
        .query_by_id(deprecated_entry["id"])
        .thenReturn(deprecated_entry)
    )
    when(bibliography_repository).query_by_id("MISSING_ID").thenRaise(NotFoundError)

    with pytest.raises(NotFoundError, match="redirect target MISSING_ID not found"):
        bibliography.find(deprecated_entry["id"])


def test_find_rejects_redirect_loop(bibliography, bibliography_repository, when):
    first_entry = BibliographyEntryFactory.build(
        id="DUPLICATE_A", deprecated=True, redirectTo="DUPLICATE_B"
    )
    second_entry = BibliographyEntryFactory.build(
        id="DUPLICATE_B", deprecated=True, redirectTo="DUPLICATE_A"
    )
    when(bibliography_repository).query_by_id("DUPLICATE_A").thenReturn(first_entry)
    when(bibliography_repository).query_by_id("DUPLICATE_B").thenReturn(second_entry)

    with pytest.raises(DuplicateError, match="redirect loop"):
        bibliography.find(first_entry["id"])


def test_find_by_citation_key(bibliography, bibliography_repository, when):
    bibliography_entry = BibliographyEntryFactory.build(citationKey="miccadei2002")
    (
        when(bibliography_repository)
        .query_by_id(bibliography_entry["citationKey"])
        .thenRaise(NotFoundError)
    )
    (
        when(bibliography_repository)
        .query_by_citation_key(bibliography_entry["citationKey"])
        .thenReturn(bibliography_entry)
    )

    assert bibliography.find(bibliography_entry["citationKey"]) == bibliography_entry


def test_find_by_alias(bibliography, bibliography_repository, when):
    alias = "legacy-id"
    bibliography_entry = BibliographyEntryFactory.build(
        aliases=[{"value": alias, "normalizedValue": alias}]
    )
    (when(bibliography_repository).query_by_id(alias).thenRaise(NotFoundError))
    (
        when(bibliography_repository)
        .query_by_citation_key(alias)
        .thenRaise(NotFoundError)
    )
    (when(bibliography_repository).query_by_alias(alias).thenReturn(bibliography_entry))

    assert bibliography.find(alias) == bibliography_entry


def test_find_canonical_id_takes_precedence_over_alias(
    bibliography, bibliography_repository, when
):
    shared_lookup = "Q30000000"
    bibliography_entry = BibliographyEntryFactory.build(id=shared_lookup)
    (
        when(bibliography_repository)
        .query_by_id(shared_lookup)
        .thenReturn(bibliography_entry)
    )

    assert bibliography.find(shared_lookup) == bibliography_entry
    verify(bibliography_repository, times=0).query_by_citation_key(shared_lookup)
    verify(bibliography_repository, times=0).query_by_alias(shared_lookup)


def test_find_citation_key_takes_precedence_over_alias(
    bibliography, bibliography_repository, when
):
    shared_lookup = "miccadei2002"
    bibliography_entry = BibliographyEntryFactory.build(citationKey=shared_lookup)
    (when(bibliography_repository).query_by_id(shared_lookup).thenRaise(NotFoundError))
    (
        when(bibliography_repository)
        .query_by_citation_key(shared_lookup)
        .thenReturn(bibliography_entry)
    )

    assert bibliography.find(shared_lookup) == bibliography_entry
    verify(bibliography_repository, times=0).query_by_alias(shared_lookup)


def test_entry_not_found(bibliography, bibliography_repository, when):
    bibliography_entry = BibliographyEntryFactory.build()
    (
        when(bibliography_repository)
        .query_by_id(bibliography_entry["id"])
        .thenRaise(NotFoundError)
    )
    with pytest.raises(NotFoundError):
        bibliography.find(bibliography_entry["id"])


def test_find_rejects_redirect_chain_over_max_depth(
    bibliography, bibliography_repository, when
):
    deprecated_entries = [
        BibliographyEntryFactory.build(
            id=f"DUPLICATE_{index}",
            deprecated=True,
            redirectTo=f"DUPLICATE_{index + 1}",
        )
        for index in range(MAX_REDIRECT_DEPTH + 1)
    ]

    for entry in deprecated_entries:
        when(bibliography_repository).query_by_id(entry["id"]).thenReturn(entry)

    with pytest.raises(DuplicateError, match="maximum depth"):
        bibliography.find(deprecated_entries[0]["id"])
