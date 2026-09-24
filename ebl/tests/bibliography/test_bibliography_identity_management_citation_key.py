import falcon
import pytest

from ebl.bibliography.application.lookup_reservation import LookupReservationState
from ebl.tests.bibliography.identity_management_test_helpers import (
    admin_client,
    body,
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


def test_add_citation_key(client, database, bibliography, user):
    entry(bibliography, user, "Q30000030")

    result = manage_identity(client, "Q30000030", {"citationKey": "added1999Key"})

    assert result.status == falcon.HTTP_OK
    assert body(result)["citationKey"] == "added1999Key"
    assert stored(database, "Q30000030")["citationKey"] == "added1999Key"
    assert reservation_state(database, "added1999Key") == COMMITTED
    assert bibliography.find("added1999Key")["id"] == "Q30000030"


def test_replace_citation_key_transitions_reservations(
    client, database, bibliography, user
):
    entry(bibliography, user, "Q30000031", citationKey="old1999Key")

    result = manage_identity(client, "Q30000031", {"citationKey": "new1999Key"})

    assert result.status == falcon.HTTP_OK
    assert stored(database, "Q30000031")["citationKey"] == "new1999Key"
    assert reservation_state(database, "new1999Key") == COMMITTED
    assert reservation_state(database, "old1999Key") == ABANDONED


def test_remove_citation_key(client, database, bibliography, user):
    entry(bibliography, user, "Q30000032", citationKey="removable1999Key")

    result = manage_identity(client, "Q30000032", {"citationKey": None})

    assert result.status == falcon.HTTP_OK
    assert "citationKey" not in body(result)
    assert "citationKey" not in stored(database, "Q30000032")
    assert reservation_state(database, "removable1999Key") == ABANDONED


def test_conflicting_citation_key_is_rejected(client, database, bibliography, user):
    entry(bibliography, user, "Q30000033", citationKey="contested1999Key")
    entry(bibliography, user, "Q30000034", citationKey="own1999Key")

    result = manage_identity(client, "Q30000034", {"citationKey": "contested1999Key"})

    assert result.status == falcon.HTTP_CONFLICT
    assert stored(database, "Q30000034")["citationKey"] == "own1999Key"
    assert reservation_state(database, "contested1999Key") == COMMITTED


def test_setting_the_same_citation_key_is_a_no_op(client, database, bibliography, user):
    entry(bibliography, user, "Q30000035", citationKey="stable1999Key")
    changelog_before = database["changelog"].count_documents(
        {"resource_id": "Q30000035"}
    )

    result = manage_identity(client, "Q30000035", {"citationKey": "stable1999Key"})

    assert result.status == falcon.HTTP_OK
    assert stored(database, "Q30000035")["citationKey"] == "stable1999Key"
    assert reservation_state(database, "stable1999Key") == COMMITTED
    assert (
        database["changelog"].count_documents({"resource_id": "Q30000035"})
        == changelog_before
    )


def test_empty_citation_key_is_rejected_by_the_schema(
    client, database, bibliography, user
):
    entry(bibliography, user, "Q30000036", citationKey="kept1999Key")

    result = manage_identity(client, "Q30000036", {"citationKey": ""})

    assert result.status == falcon.HTTP_BAD_REQUEST
    assert stored(database, "Q30000036")["citationKey"] == "kept1999Key"
