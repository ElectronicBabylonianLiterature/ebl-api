import pydash  # pyre-ignore
import pytest  # pyre-ignore
from freezegun import freeze_time  # pyre-ignore

from ebl.errors import DataError, DuplicateError, NotFoundError
from ebl.tests.factories.bibliography import ReferenceWithDocumentFactory


@pytest.fixture
def mongo_entry(bibliography_entry):
    return pydash.map_keys(
        bibliography_entry, lambda _, key: "_id" if key == "id" else key
    )


COLLECTION = "bibliography"


def test_create_and_find(bibliography, bibliography_entry, user):
    bibliography.create(bibliography_entry, user)

    assert bibliography.find(bibliography_entry["id"]) == bibliography_entry


def test_create_duplicate(bibliography, bibliography_entry, user):
    bibliography.create(bibliography_entry, user)
    with pytest.raises(DuplicateError):
        bibliography.create(bibliography_entry, user)


def test_entry_not_found(bibliography):
    with pytest.raises(NotFoundError):
        bibliography.find("not found")


def test_update(bibliography, bibliography_entry, user):
    updated_entry = pydash.omit({**bibliography_entry, "title": "New Title"}, "PMID")
    bibliography.create(bibliography_entry, user)
    bibliography.update(updated_entry, user)

    assert bibliography.find(bibliography_entry["id"]) == updated_entry


@freeze_time("2018-09-07 15:41:24.032")
def test_changelog(
    bibliography, database, bibliography_entry, mongo_entry, user, make_changelog_entry,
):

    updated_entry = {**bibliography_entry, "title": "New Title"}
    bibliography.create(bibliography_entry, user)
    bibliography.update(updated_entry, user)

    expected_changelog = [
        make_changelog_entry(
            COLLECTION,
            bibliography_entry["id"],
            {"_id": bibliography_entry["id"]},
            mongo_entry,
        ),
        make_changelog_entry(
            COLLECTION,
            bibliography_entry["id"],
            mongo_entry,
            pydash.map_keys(
                updated_entry, lambda _, key: ("_id" if key == "id" else key)
            ),
        ),
    ]

    assert [
        change
        for change in database["changelog"].find(
            {"resource_id": bibliography_entry["id"]}, {"_id": 0}
        )
    ] == expected_changelog


def test_update_not_found(bibliography, bibliography_entry, user):
    with pytest.raises(NotFoundError):
        bibliography.update(bibliography_entry, user)


def test_validate_references(bibliography, user):
    reference = ReferenceWithDocumentFactory.build()
    bibliography.create(reference.document, user)
    bibliography.validate_references([reference])


def test_validate_references_invalid(bibliography, user):
    valid_reference = ReferenceWithDocumentFactory.build()
    first_invalid = ReferenceWithDocumentFactory.build()
    second_invalid = ReferenceWithDocumentFactory.build()
    bibliography.create(valid_reference.document, user)
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
