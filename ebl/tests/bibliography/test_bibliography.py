import pytest
from mockito import verify

from ebl.errors import DataError, Defect, DuplicateError, NotFoundError
from ebl.tests.factories.bibliography import ReferenceFactory, BibliographyEntryFactory

COLLECTION = "bibliography"


def test_search_container_short_collection_number(
    bibliography, bibliography_repository, when
):
    bibliography_entry = BibliographyEntryFactory.build()
    container_title = bibliography_entry["container-title-short"]
    collection_number = bibliography_entry["collection-number"]
    query = f"{container_title} {collection_number}"
    (
        when(bibliography_repository)
        .query_by_author_year_and_title(container_title, int(collection_number), None)
        .thenReturn([])
    )
    (
        when(bibliography_repository)
        .query_by_container_title_and_collection_number(
            container_title, collection_number
        )
        .thenReturn([bibliography_entry])
    )
    assert [bibliography_entry] == bibliography.search(query)


def test_search_title_short_volume(bibliography, bibliography_repository, when):
    bibliography_entry = BibliographyEntryFactory.build()
    title_short = bibliography_entry["title-short"]
    volume = bibliography_entry["volume"]
    query = f"{title_short} {volume}"
    (
        when(bibliography_repository)
        .query_by_author_year_and_title(title_short, int(volume), None)
        .thenReturn([])
    )
    (
        when(bibliography_repository)
        .query_by_title_short_and_volume(title_short, volume)
        .thenReturn([bibliography_entry])
    )
    assert [bibliography_entry] == bibliography.search(query)


def test_search_author_title_year(bibliography, bibliography_repository, when):
    bibliography_entry = BibliographyEntryFactory.build()
    author = bibliography_entry["author"][0]["family"]
    year = bibliography_entry["issued"]["date-parts"][0][0]
    title = bibliography_entry["title"]
    query = f"{author} {year} {title}"
    (
        when(bibliography_repository)
        .query_by_author_year_and_title(author, year, title)
        .thenReturn([bibliography_entry])
    )
    (
        verify(
            bibliography_repository, 0
        ).query_by_container_title_and_collection_number(author, str(year))
    )
    assert [bibliography_entry] == bibliography.search(query)


def test_search_excludes_deprecated_entries(
    bibliography, bibliography_repository, when
):
    canonical_entry = BibliographyEntryFactory.build(id="CANONICAL_ID")
    deprecated_entry = BibliographyEntryFactory.build(
        id="DUPLICATE_ID", deprecated=True, redirectTo="CANONICAL_ID"
    )
    author = canonical_entry["author"][0]["family"]
    year = canonical_entry["issued"]["date-parts"][0][0]
    title = canonical_entry["title"]
    (
        when(bibliography_repository)
        .query_by_author_year_and_title(author, year, title)
        .thenReturn([deprecated_entry, canonical_entry])
    )

    assert bibliography.search(f"{author} {year} {title}") == [canonical_entry]


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


def test_create(
    bibliography,
    bibliography_repository,
    user,
    changelog,
    when,
    create_mongo_bibliography_entry,
):
    bibliography_entry = BibliographyEntryFactory.build()
    created_id = bibliography_entry["id"]
    (
        when(changelog)
        .create(
            COLLECTION,
            user.profile,
            {"_id": bibliography_entry["id"]},
            create_mongo_bibliography_entry(),
        )
        .thenReturn()
    )
    (when(bibliography_repository).create(bibliography_entry).thenReturn(created_id))

    assert bibliography.create(bibliography_entry, user) == created_id


def test_create_rejects_mismatched_repository_id(
    bibliography, bibliography_repository, user, when
):
    bibliography_entry = BibliographyEntryFactory.build()
    (
        when(bibliography_repository)
        .create(bibliography_entry)
        .thenReturn("DIFFERENT_ID")
    )

    with pytest.raises(Defect, match="does not match"):
        bibliography.create(bibliography_entry, user)


def test_create_duplicate(
    bibliography,
    user,
    when,
    changelog,
    bibliography_repository,
    create_mongo_bibliography_entry,
):
    bibliography_entry = BibliographyEntryFactory.build()
    (
        when(changelog)
        .create(
            COLLECTION,
            user.profile,
            {"_id": bibliography_entry["id"]},
            create_mongo_bibliography_entry(),
        )
        .thenReturn()
    )
    (when(bibliography_repository).create(bibliography_entry).thenRaise(DuplicateError))
    with pytest.raises(DuplicateError):
        bibliography.create(bibliography_entry, user)
    verify(changelog, times=0).create(
        COLLECTION,
        user.profile,
        {"_id": bibliography_entry["id"]},
        create_mongo_bibliography_entry(),
    )


def test_entry_not_found(bibliography, bibliography_repository, when):
    bibliography_entry = BibliographyEntryFactory.build()
    (
        when(bibliography_repository)
        .query_by_id(bibliography_entry["id"])
        .thenRaise(NotFoundError)
    )
    with pytest.raises(NotFoundError):
        bibliography.find(bibliography_entry["id"])


def test_update(
    bibliography,
    bibliography_repository,
    user,
    when,
    changelog,
    create_mongo_bibliography_entry,
):
    bibliography_entry = BibliographyEntryFactory.build()
    (
        when(bibliography_repository)
        .query_by_id(bibliography_entry["id"])
        .thenReturn(bibliography_entry)
    )
    (
        when(changelog)
        .create(
            COLLECTION,
            user.profile,
            create_mongo_bibliography_entry(),
            create_mongo_bibliography_entry(),
        )
        .thenReturn()
    )
    (when(bibliography_repository).update(bibliography_entry).thenReturn())
    bibliography.update(bibliography_entry, user)


def test_update_not_found(bibliography_repository, bibliography, user, when):
    bibliography_entry = BibliographyEntryFactory.build()
    (
        when(bibliography_repository)
        .query_by_id(bibliography_entry["id"])
        .thenRaise(NotFoundError)
    )
    with pytest.raises(NotFoundError):
        bibliography.update(bibliography_entry, user)


def test_validate_references(
    bibliography_repository, bibliography, user, changelog, when
):
    reference = ReferenceFactory.build(with_document=True)

    (when(bibliography).find(reference.id).thenReturn(reference))
    bibliography.validate_references([reference])


def test_validate_references_invalid(
    bibliography_repository, bibliography, user, changelog, when
):
    valid_reference = ReferenceFactory.build(with_document=True)
    first_invalid = ReferenceFactory.build(with_document=True)
    second_invalid = ReferenceFactory.build(with_document=True)
    bibliography.create(valid_reference.document, user)
    (when(bibliography).find(valid_reference.id).thenReturn(valid_reference))
    (when(bibliography).find(first_invalid.id).thenRaise(NotFoundError))
    (when(bibliography).find(second_invalid.id).thenRaise(NotFoundError))

    expected_error = (
        f"Unknown bibliography entries: {first_invalid.id}, {second_invalid.id}."
    )

    with pytest.raises(DataError, match=expected_error):
        bibliography.validate_references(
            [first_invalid, valid_reference, second_invalid]
        )


def test_list_all_signs(bibliography, bibliography_repository, user) -> None:
    bibliography_entry = BibliographyEntryFactory.build()
    bibliography.create(bibliography_entry, user)
    assert bibliography.list_all_bibliography() == [bibliography_entry["id"]]
