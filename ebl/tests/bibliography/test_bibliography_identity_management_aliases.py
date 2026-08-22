import falcon
import pytest

from ebl.bibliography.application.lookup_reservation import LookupReservationState
from ebl.tests.bibliography.identity_management_test_helpers import (
    admin_client,
    alias,
    body,
    description,
    entry,
    manage_identity,
    reservation_state,
    stored,
)

COMMITTED = LookupReservationState.COMMITTED.value
ABANDONED = LookupReservationState.ABANDONED.value


@pytest.fixture
def client(context):
    return admin_client(context)


def test_add_single_alias(client, context, database, bibliography, user):
    entry(bibliography, user, "Q30000010")

    result = manage_identity(client, "Q30000010", {"addAliases": [alias("added-one")]})

    assert result.status == falcon.HTTP_OK
    assert body(result)["aliases"] == [alias("added-one")]
    assert stored(database, "Q30000010")["aliases"] == [alias("added-one")]
    assert bibliography.find("added-one")["id"] == "Q30000010"


def test_add_multiple_aliases(client, database, bibliography, user):
    entry(bibliography, user, "Q30000011")

    result = manage_identity(
        client,
        "Q30000011",
        {"addAliases": [alias("multi-a"), alias("multi-b")]},
    )

    assert result.status == falcon.HTTP_OK
    assert stored(database, "Q30000011")["aliases"] == [
        alias("multi-a"),
        alias("multi-b"),
    ]
    assert reservation_state(database, "multi-a") == COMMITTED
    assert reservation_state(database, "multi-b") == COMMITTED


def test_add_alias_preserves_every_alias_field(client, database, bibliography, user):
    entry(bibliography, user, "Q30000012")
    full_alias = {
        "value": "Full Alias",
        "normalizedValue": "full-alias",
        "type": "partner_id",
        "source": "partner_request",
        "status": "redirect",
    }

    manage_identity(client, "Q30000012", {"addAliases": [full_alias]})

    assert stored(database, "Q30000012")["aliases"] == [full_alias]


def test_add_alias_does_not_invent_provenance(client, database, bibliography, user):
    entry(bibliography, user, "Q30000013")

    manage_identity(client, "Q30000013", {"addAliases": [{"value": "bare-alias"}]})

    assert stored(database, "Q30000013")["aliases"] == [{"value": "bare-alias"}]


def test_remove_alias_retires_reservation(client, database, bibliography, user):
    entry(bibliography, user, "Q30000014", aliases=[alias("removable")])
    assert reservation_state(database, "removable") == COMMITTED

    result = manage_identity(client, "Q30000014", {"removeAliases": ["removable"]})

    assert result.status == falcon.HTTP_OK
    assert stored(database, "Q30000014")["aliases"] == []
    assert reservation_state(database, "removable") == ABANDONED


def test_replace_alias_in_one_operation(client, database, bibliography, user):
    entry(bibliography, user, "Q30000015", aliases=[alias("typo-alias")])

    result = manage_identity(
        client,
        "Q30000015",
        {"removeAliases": ["typo-alias"], "addAliases": [alias("fixed-alias")]},
    )

    assert result.status == falcon.HTTP_OK
    assert stored(database, "Q30000015")["aliases"] == [alias("fixed-alias")]
    assert reservation_state(database, "typo-alias") == ABANDONED
    assert reservation_state(database, "fixed-alias") == COMMITTED


def test_repair_alias_metadata_keeping_the_value(client, database, bibliography, user):
    entry(bibliography, user, "Q30000016", aliases=[alias("kept-value")])
    repaired = alias("kept-value", type="partner_id", source="partner_request")

    manage_identity(
        client,
        "Q30000016",
        {"removeAliases": ["kept-value"], "addAliases": [repaired]},
    )

    assert stored(database, "Q30000016")["aliases"] == [repaired]
    assert reservation_state(database, "kept-value") == COMMITTED


def test_removing_an_absent_alias_is_rejected(client, database, bibliography, user):
    entry(bibliography, user, "Q30000017")

    result = manage_identity(client, "Q30000017", {"removeAliases": ["not-there"]})

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert "no alias not-there" in description(result)
    assert "aliases" not in stored(database, "Q30000017")


def test_adding_a_duplicate_alias_is_rejected(client, database, bibliography, user):
    entry(bibliography, user, "Q30000018", aliases=[alias("already-here")])

    result = manage_identity(
        client, "Q30000018", {"addAliases": [alias("already-here")]}
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert "already has alias already-here" in description(result)
    assert stored(database, "Q30000018")["aliases"] == [alias("already-here")]
