import bson
import pytest
from bson import ObjectId
from freezegun import freeze_time
from pymongo.database import Database

from ebl.changelog import Changelog, create_entry, is_storable
from ebl.users.domain.user import User


COLLECTION = "changelog"
RESOURCE_TYPE = "type"
RESOURCE_ID = "id"
OLD = {"_id": RESOURCE_ID, "a": "foo", "b": "bar"}
NEW = {"_id": RESOURCE_ID, "b": "baz", "c": 43}
DIFF = [["change", "b", ["bar", "baz"]], ["add", "", [["c", 43]]]]


@freeze_time("2018-09-07 15:41:24.032")
def test_create(database, changelog, user, make_changelog_entry):
    entry_id = changelog.create(RESOURCE_TYPE, user.profile, OLD, NEW)
    expected = make_changelog_entry(RESOURCE_TYPE, RESOURCE_ID, OLD, NEW)
    assert database[COLLECTION].find_one({"_id": entry_id}, {"_id": 0}) == expected


@freeze_time("2018-09-07 15:41:24.032")
def test_insert_stores_the_entry(
    database: Database, changelog: Changelog, user: User
) -> None:
    expected = create_entry(user.profile, RESOURCE_TYPE, RESOURCE_ID, DIFF)

    entry_id = changelog.insert(
        create_entry(user.profile, RESOURCE_TYPE, RESOURCE_ID, DIFF)
    )

    assert database[COLLECTION].find_one({"_id": entry_id}, {"_id": 0}) == expected
    assert database[COLLECTION].count_documents({}) == 1


@pytest.mark.parametrize("missing_bytes,expected", [(0, True), (1, False)])
def test_entry_is_storable_up_to_the_size_limit_of_the_stored_document(
    user: User, monkeypatch: pytest.MonkeyPatch, missing_bytes: int, expected: bool
) -> None:
    entry = create_entry(user.profile, RESOURCE_TYPE, RESOURCE_ID, DIFF)
    stored_size = len(bson.encode({"_id": ObjectId(), **entry}))
    monkeypatch.setattr("ebl.changelog.MAX_BSON_SIZE", stored_size - missing_bytes)

    assert is_storable(entry) is expected
    assert "_id" not in entry


def test_entry_is_storable_within_the_size_limit_of_mongodb(user: User) -> None:
    assert is_storable(create_entry(user.profile, RESOURCE_TYPE, RESOURCE_ID, DIFF))
