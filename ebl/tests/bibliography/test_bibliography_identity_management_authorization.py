import json

import falcon
import pytest

from ebl.common.domain.scopes import Scope
from ebl.tests.bibliography.bibliography_route_test_helpers import client_with_scope
from ebl.tests.bibliography.identity_management_test_helpers import (
    ADMIN_SCOPE,
    admin_client,
    alias,
    entry,
    manage_identity,
    stored,
)

PARTNER_M2M_SCOPE = "export:bibliography write:bibliography"


@pytest.fixture
def subject(bibliography, user):
    return entry(bibliography, user, "Q30000080")


def test_admin_scope_succeeds(context, database, subject):
    result = manage_identity(
        admin_client(context), "Q30000080", {"addAliases": [alias("admin-added")]}
    )

    assert result.status == falcon.HTTP_OK
    assert stored(database, "Q30000080")["aliases"] == [alias("admin-added")]


def test_guest_is_forbidden(guest_client, database, subject):
    result = manage_identity(
        guest_client, "Q30000080", {"addAliases": [alias("guest-added")]}
    )

    assert result.status == falcon.HTTP_FORBIDDEN
    assert "aliases" not in stored(database, "Q30000080")


def test_bibliography_write_scope_alone_is_forbidden(context, database, subject):
    client = client_with_scope(context, "write:bibliography")

    result = manage_identity(
        client, "Q30000080", {"addAliases": [alias("writer-added")]}
    )

    assert result.status == falcon.HTTP_FORBIDDEN
    assert "aliases" not in stored(database, "Q30000080")


def test_partner_m2m_scopes_cannot_reach_the_operation(context, database, subject):
    client = client_with_scope(context, PARTNER_M2M_SCOPE)

    result = manage_identity(
        client, "Q30000080", {"addAliases": [alias("partner-added")]}
    )

    assert result.status == falcon.HTTP_FORBIDDEN
    assert "aliases" not in stored(database, "Q30000080")


def test_duplicate_check_scope_is_forbidden(context, database, subject):
    client = client_with_scope(context, "check:bibliography_duplicates")

    result = manage_identity(client, "Q30000080", {"citationKey": "checker1999Key"})

    assert result.status == falcon.HTTP_FORBIDDEN
    assert "citationKey" not in stored(database, "Q30000080")


def test_admin_scope_does_not_grant_ordinary_bibliography_write(context, subject):
    client = client_with_scope(context, ADMIN_SCOPE)

    result = client.simulate_post(
        "/bibliography/Q30000080", body=json.dumps({**subject, "title": "New"})
    )

    assert result.status == falcon.HTTP_FORBIDDEN


def test_admin_bibliography_scope_is_restricted():
    assert Scope.from_string(ADMIN_SCOPE).is_restricted
    assert str(Scope.ADMIN_BIBLIOGRAPHY) == ADMIN_SCOPE
