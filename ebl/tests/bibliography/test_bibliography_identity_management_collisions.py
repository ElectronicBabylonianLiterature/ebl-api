import falcon
import pytest

from ebl.tests.bibliography.identity_management_test_helpers import (
    RESERVATIONS,
    admin_client,
    alias,
    entry,
    manage_identity,
    reservation,
    stored,
)


@pytest.fixture
def client(context):
    return admin_client(context)


@pytest.fixture
def subject(bibliography, user):
    return entry(bibliography, user, "Q30000020")


def assert_unchanged_identity(database, before: dict) -> None:
    after = stored(database, before["_id"])
    for field in ("aliases", "citationKey", "deprecated", "redirectTo"):
        assert after.get(field) == before.get(field)


def test_alias_colliding_with_another_canonical_id(
    client, database, bibliography, user, subject
):
    entry(bibliography, user, "Q30000021")
    before = stored(database, "Q30000020")

    result = manage_identity(client, "Q30000020", {"addAliases": [alias("Q30000021")]})

    assert result.status == falcon.HTTP_CONFLICT
    assert_unchanged_identity(database, before)


def test_alias_colliding_with_another_citation_key(
    client, database, bibliography, user, subject
):
    entry(bibliography, user, "Q30000022", citationKey="taken-key")
    before = stored(database, "Q30000020")

    result = manage_identity(client, "Q30000020", {"addAliases": [alias("taken-key")]})

    assert result.status == falcon.HTTP_CONFLICT
    assert_unchanged_identity(database, before)


def test_alias_colliding_with_another_alias(
    client, database, bibliography, user, subject
):
    entry(bibliography, user, "Q30000023", aliases=[alias("taken-alias")])
    before = stored(database, "Q30000020")

    result = manage_identity(
        client, "Q30000020", {"addAliases": [alias("taken-alias")]}
    )

    assert result.status == falcon.HTTP_CONFLICT
    assert_unchanged_identity(database, before)


def test_alias_colliding_on_normalized_value(
    client, database, bibliography, user, subject
):
    entry(
        bibliography,
        user,
        "Q30000024",
        aliases=[{"value": "Dossin 1967", "normalizedValue": "dossin-1967"}],
    )
    before = stored(database, "Q30000020")

    result = manage_identity(
        client,
        "Q30000020",
        {"addAliases": [{"value": "Other", "normalizedValue": "dossin-1967"}]},
    )

    assert result.status == falcon.HTTP_CONFLICT
    assert_unchanged_identity(database, before)


def test_citation_key_colliding_with_another_alias(
    client, database, bibliography, user, subject
):
    entry(bibliography, user, "Q30000025", aliases=[alias("alias-as-key")])
    before = stored(database, "Q30000020")

    result = manage_identity(client, "Q30000020", {"citationKey": "alias-as-key"})

    assert result.status == falcon.HTTP_CONFLICT
    assert_unchanged_identity(database, before)


def test_collision_leaves_no_pending_reservation(
    client, database, bibliography, user, subject
):
    entry(bibliography, user, "Q30000026", aliases=[alias("contested")])

    manage_identity(
        client,
        "Q30000020",
        {"addAliases": [alias("kept-clean"), alias("contested")]},
    )

    contested = reservation(database, "contested")
    assert contested is not None
    assert contested["entryId"] == "Q30000026"
    assert database[RESERVATIONS].count_documents({"state": "pending"}) == 0
    assert reservation(database, "kept-clean") is None


def test_collision_writes_no_changelog_entry(
    client, database, bibliography, user, subject
):
    entry(bibliography, user, "Q30000027", aliases=[alias("blocked")])
    before = database["changelog"].count_documents({"resource_id": "Q30000020"})

    manage_identity(client, "Q30000020", {"addAliases": [alias("blocked")]})

    assert database["changelog"].count_documents({"resource_id": "Q30000020"}) == before
