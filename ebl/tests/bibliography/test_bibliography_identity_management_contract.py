import json

import falcon
import pytest

from ebl.tests.bibliography.identity_management_test_helpers import (
    admin_client,
    alias,
    body,
    entry,
    manage_identity,
    stored,
)


@pytest.fixture
def client(context):
    return admin_client(context)


@pytest.fixture
def subject(bibliography, user):
    return entry(bibliography, user, "Q30000110", citationKey="subject1999Key")


def test_canonical_id_cannot_be_submitted(client, database, subject):
    result = manage_identity(client, "Q30000110", {"id": "Q30000999"})

    assert result.status == falcon.HTTP_BAD_REQUEST
    assert stored(database, "Q30000110") is not None
    assert database["bibliography"].count_documents({"_id": "Q30000999"}) == 0


def test_canonical_id_is_unchanged_by_an_identity_change(client, database, subject):
    manage_identity(client, "Q30000110", {"addAliases": [alias("id-stable")]})

    assert stored(database, "Q30000110")["_id"] == "Q30000110"
    assert database["bibliography"].count_documents({}) == 1


def test_csl_metadata_cannot_be_submitted(client, database, subject):
    result = manage_identity(client, "Q30000110", {"title": "Rewritten"})

    assert result.status == falcon.HTTP_BAD_REQUEST
    assert stored(database, "Q30000110")["title"] == subject["title"]


def test_raw_deprecated_field_cannot_be_submitted(client, database, subject):
    result = manage_identity(client, "Q30000110", {"deprecated": True})

    assert result.status == falcon.HTTP_BAD_REQUEST
    assert "deprecated" not in stored(database, "Q30000110")


def test_raw_redirect_to_field_cannot_be_submitted(client, database, subject):
    result = manage_identity(client, "Q30000110", {"redirectTo": "Q30000111"})

    assert result.status == falcon.HTTP_BAD_REQUEST
    assert "redirectTo" not in stored(database, "Q30000110")


def test_empty_payload_is_rejected(client, subject):
    assert manage_identity(client, "Q30000110", {}).status == falcon.HTTP_BAD_REQUEST


def test_empty_alias_arrays_are_rejected(client, subject):
    assert (
        manage_identity(client, "Q30000110", {"addAliases": []}).status
        == falcon.HTTP_BAD_REQUEST
    )
    assert (
        manage_identity(client, "Q30000110", {"removeAliases": []}).status
        == falcon.HTTP_BAD_REQUEST
    )


def test_alias_without_a_value_is_rejected(client, subject):
    result = manage_identity(client, "Q30000110", {"addAliases": [{"type": "x"}]})

    assert result.status == falcon.HTTP_BAD_REQUEST


def test_unknown_alias_field_is_rejected(client, subject):
    result = manage_identity(
        client, "Q30000110", {"addAliases": [{"value": "a", "project": "x"}]}
    )

    assert result.status == falcon.HTTP_BAD_REQUEST


def test_reactivate_false_is_rejected(client, subject):
    result = manage_identity(client, "Q30000110", {"reactivate": False})

    assert result.status == falcon.HTTP_BAD_REQUEST


def test_unknown_record_is_not_found(client):
    result = manage_identity(client, "Q39999999", {"addAliases": [alias("orphan")]})

    assert result.status == falcon.HTTP_NOT_FOUND


def test_response_returns_the_resulting_entry(client, subject):
    result = manage_identity(client, "Q30000110", {"addAliases": [alias("returned")]})

    assert result.status == falcon.HTTP_OK
    assert body(result)["id"] == "Q30000110"
    assert body(result)["citationKey"] == "subject1999Key"
    assert body(result)["aliases"] == [alias("returned")]
    assert body(result)["title"] == subject["title"]


def test_identity_route_is_distinct_from_the_metadata_route(client, database, subject):
    result = client.simulate_post(
        "/bibliography/Q30000110", body=json.dumps({**subject, "title": "Metadata"})
    )

    assert result.status == falcon.HTTP_FORBIDDEN
    assert stored(database, "Q30000110")["title"] == subject["title"]
