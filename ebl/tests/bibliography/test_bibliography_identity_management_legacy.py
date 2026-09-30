import falcon
import pytest

from ebl.bibliography.application.lookup_reservation import LookupReservationState
from ebl.tests.bibliography.identity_management_test_helpers import (
    RESERVATIONS,
    admin_client,
    alias,
    entry,
    manage_identity,
    reservation,
    reservation_state,
    stored,
)

COMMITTED = LookupReservationState.COMMITTED.value


@pytest.fixture
def client(context):
    return admin_client(context)


def drop_reservations(database, id_: str) -> None:
    database[RESERVATIONS].delete_many({"entryId": id_})


def legacy_entry(bibliography, database, user, id_: str, **overrides) -> dict:
    created = entry(bibliography, user, id_, **overrides)
    drop_reservations(database, id_)
    return created


def test_add_alias_to_a_legacy_record_without_reservations(
    client, database, bibliography, user
):
    legacy_entry(bibliography, database, user, "Q30000100", citationKey="legacy1999Key")
    assert reservation(database, "legacy1999Key") is None

    result = manage_identity(
        client, "Q30000100", {"addAliases": [alias("legacy-added")]}
    )

    assert result.status == falcon.HTTP_OK
    assert stored(database, "Q30000100")["aliases"] == [alias("legacy-added")]
    assert reservation_state(database, "legacy-added") == COMMITTED


def test_remove_a_legacy_alias_that_has_no_reservation(
    client, database, bibliography, user
):
    legacy_entry(
        bibliography, database, user, "Q30000101", aliases=[alias("legacy-alias")]
    )
    assert reservation(database, "legacy-alias") is None

    result = manage_identity(client, "Q30000101", {"removeAliases": ["legacy-alias"]})

    assert result.status == falcon.HTTP_OK
    assert stored(database, "Q30000101")["aliases"] == []
    assert reservation(database, "legacy-alias") is None


def test_replace_a_legacy_citation_key_without_reservation(
    client, database, bibliography, user
):
    legacy_entry(bibliography, database, user, "Q30000102", citationKey="old1999Key")

    result = manage_identity(client, "Q30000102", {"citationKey": "new1999Key"})

    assert result.status == falcon.HTTP_OK
    assert stored(database, "Q30000102")["citationKey"] == "new1999Key"
    assert reservation_state(database, "new1999Key") == COMMITTED
    assert reservation(database, "old1999Key") is None


def test_legacy_unreserved_value_still_blocks_a_colliding_claim(
    client, database, bibliography, user
):
    legacy_entry(
        bibliography, database, user, "Q30000103", aliases=[alias("legacy-taken")]
    )
    entry(bibliography, user, "Q30000104")

    result = manage_identity(
        client, "Q30000104", {"addAliases": [alias("legacy-taken")]}
    )

    assert result.status == falcon.HTTP_CONFLICT
    assert "aliases" not in stored(database, "Q30000104")


def test_duplicate_merge_aliases_on_a_legacy_record(
    client, database, bibliography, user
):
    legacy_entry(
        bibliography,
        database,
        user,
        "Q30000105",
        aliases=[alias("merged-one"), alias("merged-two")],
    )

    result = manage_identity(
        client,
        "Q30000105",
        {"removeAliases": ["merged-one"], "addAliases": [alias("merged-three")]},
    )

    assert result.status == falcon.HTTP_OK
    assert stored(database, "Q30000105")["aliases"] == [
        alias("merged-two"),
        alias("merged-three"),
    ]
    assert reservation_state(database, "merged-three") == COMMITTED


def test_deprecate_a_legacy_record_without_reservations(
    client, database, bibliography, user
):
    legacy_entry(bibliography, database, user, "Q30000106")
    entry(bibliography, user, "Q30000107")

    result = manage_identity(client, "Q30000106", {"deprecateTo": "Q30000107"})

    assert result.status == falcon.HTTP_OK
    assert bibliography.find("Q30000106")["id"] == "Q30000107"
