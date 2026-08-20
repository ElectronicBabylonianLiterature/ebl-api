import falcon
import pytest

from ebl.tests.bibliography.identity_management_test_helpers import (
    admin_client,
    alias,
    changelog_entries,
    entry,
    manage_identity,
)


@pytest.fixture
def client(context):
    return admin_client(context)


def latest_diff(database, id_: str):
    return changelog_entries(database, id_)[-1]


def test_alias_change_is_audited(client, database, bibliography, user):
    entry(bibliography, user, "Q30000140")

    manage_identity(client, "Q30000140", {"addAliases": [alias("audited")]})

    changelog_entry = latest_diff(database, "Q30000140")
    assert changelog_entry["resource_type"] == "bibliography"
    assert changelog_entry["resource_id"] == "Q30000140"
    assert changelog_entry["user_profile"]["name"] == "Test User"
    assert changelog_entry["date"]
    assert ["add", "", [["aliases", [alias("audited")]]]] in changelog_entry["diff"]


def test_citation_key_change_records_before_and_after(
    client, database, bibliography, user
):
    entry(bibliography, user, "Q30000141", citationKey="before1999Key")

    manage_identity(client, "Q30000141", {"citationKey": "after1999Key"})

    changelog_entry = latest_diff(database, "Q30000141")
    assert [
        "change",
        "citationKey",
        ["before1999Key", "after1999Key"],
    ] in changelog_entry["diff"]


def test_deprecation_is_audited(client, database, bibliography, user):
    entry(bibliography, user, "Q30000142")
    entry(bibliography, user, "Q30000143")

    manage_identity(client, "Q30000142", {"deprecateTo": "Q30000143"})

    diff = latest_diff(database, "Q30000142")["diff"]
    added = [change for change in diff if change[0] == "add"]
    assert any("deprecated" in str(change) for change in added)
    assert any("redirectTo" in str(change) for change in added)


def test_each_successful_change_adds_exactly_one_entry(
    client, database, bibliography, user
):
    entry(bibliography, user, "Q30000144")
    before = len(changelog_entries(database, "Q30000144"))

    manage_identity(client, "Q30000144", {"addAliases": [alias("first")]})
    manage_identity(client, "Q30000144", {"addAliases": [alias("second")]})

    assert len(changelog_entries(database, "Q30000144")) == before + 2


def test_validation_failure_writes_no_changelog_entry(
    client, database, bibliography, user
):
    entry(bibliography, user, "Q30000145")
    before = len(changelog_entries(database, "Q30000145"))

    result = manage_identity(client, "Q30000145", {"removeAliases": ["absent"]})

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert len(changelog_entries(database, "Q30000145")) == before


def test_no_op_writes_no_changelog_entry(client, database, bibliography, user):
    entry(bibliography, user, "Q30000146")
    before = len(changelog_entries(database, "Q30000146"))

    result = manage_identity(client, "Q30000146", {"reactivate": True})

    assert result.status == falcon.HTTP_OK
    assert len(changelog_entries(database, "Q30000146")) == before
