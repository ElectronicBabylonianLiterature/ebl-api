import pydash  # pyre-ignore
import pytest  # pyre-ignore

from ebl.errors import DataError, DuplicateError, NotFoundError
from ebl.tests.factories.bibliography import ReferenceWithDocumentFactory

COLLECTION = "bibliography"


@pytest.fixture
def mongo_entry(bibliography_entry):
    return pydash.map_keys(
        bibliography_entry, lambda _, key: "_id" if key == "id" else key
    )


def test_find(bibliography, bibliography_repository, when, bibliography_entry):
    (
        when(bibliography_repository)
        .query_by_id(bibliography_entry["id"])
        .thenReturn(bibliography_entry)
    )
    assert bibliography.find(bibliography_entry["id"]) == bibliography_entry


def test_create(bibliography, bibliography_repository, bibliography_entry, user,
                changelog, when, mongo_entry):
    (
        when(changelog)
        .create(
            COLLECTION,
            user.profile,
            {"_id": bibliography_entry["id"]},
            mongo_entry,
        ).thenReturn()
    )
    (
        when(bibliography_repository)
        .create(bibliography_entry)
        .thenReturn()
    )

    bibliography.create(bibliography_entry, user)


def test_create_duplicate(bibliography, bibliography_entry, user, when, changelog,
                          bibliography_repository, mongo_entry):
    (
        when(changelog)
        .create(
            COLLECTION,
            user.profile,
            {"_id": bibliography_entry["id"]},
            mongo_entry,
        ).thenReturn()
    )
    (
        when(bibliography_repository)
        .create(bibliography_entry)
        .thenRaise(DuplicateError)
    )
    with pytest.raises(DuplicateError):
        bibliography.create(bibliography_entry, user)


def test_entry_not_found(bibliography, bibliography_repository,
                         bibliography_entry, when):
    (
        when(bibliography_repository)
        .query_by_id(bibliography_entry["id"])
        .thenRaise(NotFoundError)
    )
    with pytest.raises(NotFoundError):
        bibliography.find(bibliography_entry["id"])


def test_update(bibliography, bibliography_repository,
                bibliography_entry, user, when, changelog, mongo_entry):
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
            mongo_entry,
            mongo_entry,
        ).thenReturn()
    )
    (
        when(bibliography_repository)
        .update(bibliography_entry)
        .thenReturn()
    )
    bibliography.update(bibliography_entry, user)


def test_update_not_found(bibliography_repository, bibliography,
                          bibliography_entry, user, when):
    (
        when(bibliography_repository)
        .query_by_id(bibliography_entry["id"])
        .thenRaise(NotFoundError)
    )
    with pytest.raises(NotFoundError):
        bibliography.update(bibliography_entry, user)


def test_validate_references(bibliography_repository, bibliography,
                             bibliography_entry, user, changelog, when):
    reference = ReferenceWithDocumentFactory.build()

    (
        when(bibliography)
        .find(reference.id)
        .thenReturn(reference)
    )
    bibliography.validate_references([reference])


def test_validate_references_invalid(bibliography_repository, bibliography,
                                     bibliography_entry, user, changelog, when):
    valid_reference = ReferenceWithDocumentFactory.build()
    first_invalid = ReferenceWithDocumentFactory.build()
    second_invalid = ReferenceWithDocumentFactory.build()
    bibliography.create(valid_reference.document, user)
    (
        when(bibliography)
        .find(valid_reference.id)
        .thenReturn(valid_reference)
    )
    (
        when(bibliography)
        .find(first_invalid.id)
        .thenRaise(NotFoundError)
    )
    (
        when(bibliography)
        .find(second_invalid.id)
        .thenRaise(NotFoundError)
    )

    expected_error = (
        "Unknown bibliography entries: "
        f"{first_invalid.id}"
        ", "
        f"{second_invalid.id}"
        "."
    )

    with pytest.raises(DataError, match=expected_error):
        bibliography.validate_references(
            [first_invalid, valid_reference, second_invalid]
        )
