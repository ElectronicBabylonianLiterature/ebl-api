"""The three bibliography write paths have three different contracts.

| route                            | metadata | raw identity state | identity commands |
| -------------------------------- | -------- | ------------------ | ----------------- |
| `POST /bibliography`             | allowed  | rejected           | rejected          |
| `POST /bibliography/{id}`        | allowed  | round-trip only    | rejected          |
| `POST /bibliography/{id}/identity` | rejected | rejected         | allowed           |
| partner create                   | allowed  | rejected           | n/a               |
"""

import falcon
import pytest

from ebl.tests.bibliography.identity_management_test_helpers import (
    admin_client,
    manage_identity,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory

RAW_IDENTITY_STATE = {"citationKey": "clientChosen"}
IDENTITY_COMMANDS = {"addAliases": [{"value": "a", "normalizedValue": "a"}]}
METADATA = {"title": "A metadata edit"}
ID = "Q30000024"


@pytest.fixture
def entry(bibliography, user):
    bibliography_entry = BibliographyEntryFactory.build(id=ID, title="Original")
    bibliography.create(bibliography_entry, user)
    return bibliography_entry


def test_create_accepts_metadata(client):
    entry_ = BibliographyEntryFactory.build(id="CREATE-1", **METADATA)

    assert client.simulate_post("/bibliography", json=entry_).status == (
        falcon.HTTP_CREATED
    )


def test_create_rejects_raw_identity_state(client):
    entry_ = BibliographyEntryFactory.build(**{"id": "CREATE-2", **RAW_IDENTITY_STATE})

    assert client.simulate_post("/bibliography", json=entry_).status == (
        falcon.HTTP_UNPROCESSABLE_ENTITY
    )


def test_create_rejects_identity_commands(client):
    entry_ = BibliographyEntryFactory.build(**{"id": "CREATE-3", **IDENTITY_COMMANDS})

    assert client.simulate_post("/bibliography", json=entry_).status == (
        falcon.HTTP_BAD_REQUEST
    )


def test_update_accepts_metadata(client, entry):
    assert client.simulate_post(
        f"/bibliography/{ID}", json={**entry, **METADATA}
    ).status == (falcon.HTTP_NO_CONTENT)


def test_update_accepts_an_unchanged_round_trip_of_identity_state(
    client, bibliography, user, aliased_entry
):
    stored = client.simulate_get(f"/bibliography/{aliased_entry['id']}").json

    result = client.simulate_post(
        f"/bibliography/{aliased_entry['id']}", json={**stored, **METADATA}
    )

    assert result.status == falcon.HTTP_NO_CONTENT
    assert bibliography.find(aliased_entry["id"])["title"] == METADATA["title"]


def test_update_rejects_mutating_identity_state(client, bibliography, aliased_entry):
    stored = client.simulate_get(f"/bibliography/{aliased_entry['id']}").json

    result = client.simulate_post(
        f"/bibliography/{aliased_entry['id']}", json={**stored, **RAW_IDENTITY_STATE}
    )

    assert result.status == falcon.HTTP_CONFLICT
    assert bibliography.find(aliased_entry["id"])["citationKey"] != "clientChosen"


def test_update_rejects_identity_commands(client, entry):
    result = client.simulate_post(
        f"/bibliography/{ID}", json={**entry, **IDENTITY_COMMANDS}
    )

    assert result.status == falcon.HTTP_BAD_REQUEST


def test_the_identity_endpoint_is_not_a_general_csl_editor(context, entry):
    result = manage_identity(
        admin_client(context), ID, {**IDENTITY_COMMANDS, **METADATA}
    )

    assert result.status == falcon.HTTP_BAD_REQUEST


def test_the_identity_endpoint_is_not_a_raw_lifecycle_replacement(context, entry):
    result = manage_identity(
        admin_client(context), ID, {"deprecated": True, "redirectTo": "OTHER"}
    )

    assert result.status == falcon.HTTP_BAD_REQUEST


def test_the_identity_endpoint_accepts_identity_commands(context, bibliography, entry):
    result = manage_identity(admin_client(context), ID, IDENTITY_COMMANDS)

    assert result.status == falcon.HTTP_OK
    assert bibliography.find("a")["id"] == ID


def test_the_identity_endpoint_is_closed_to_ordinary_bibliography_writers(
    client, entry
):
    result = manage_identity(client, ID, IDENTITY_COMMANDS)

    assert result.status == falcon.HTTP_FORBIDDEN


def test_partner_create_accepts_its_own_contract(client):
    result = client.simulate_post(
        "/api/v1/bibliography", json={"type": "book", "title": "Partner metadata"}
    )

    assert result.status == falcon.HTTP_CREATED


def test_partner_create_rejects_client_supplied_identity_state(client):
    result = client.simulate_post(
        "/api/v1/bibliography",
        json={"type": "book", "title": "Partner", **RAW_IDENTITY_STATE},
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
