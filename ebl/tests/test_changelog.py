from freezegun import freeze_time


COLLECTION = "changelog"
RESOURCE_TYPE = "type"
RESOURCE_ID = "id"
OLD = {"_id": RESOURCE_ID, "a": "foo", "b": "bar"}
NEW = {"_id": RESOURCE_ID, "b": "baz", "c": 43}


@freeze_time("2018-09-07 15:41:24.032")
def test_create(database, changelog, user, make_changelog_entry):
    entry_id = changelog.create(RESOURCE_TYPE, user.profile, OLD, NEW)
    expected = make_changelog_entry(RESOURCE_TYPE, RESOURCE_ID, OLD, NEW)
    assert database[COLLECTION].find_one({"_id": entry_id}, {"_id": 0}) == expected
