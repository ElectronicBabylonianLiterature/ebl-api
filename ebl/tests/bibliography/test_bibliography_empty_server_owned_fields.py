import falcon
import pytest

from ebl.tests.bibliography.identity_preservation_test_helpers import (
    CITATION_KEY,
    post_entry,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory
from ebl.users.domain.user import User

ENTRY_ID = "SC0001"
ALIAS_A = {
    "value": "alias-a",
    "normalizedValue": "alias-a",
    "type": "legacy_id",
    "source": "duplicate_merge_2026-08-04",
    "status": "redirect",
}
ALIAS_B = {**ALIAS_A, "value": "alias-b", "normalizedValue": "alias-b"}


@pytest.fixture
def plain_entry(bibliography, user: User) -> dict:
    entry = BibliographyEntryFactory.build(id=ENTRY_ID, title="No identity state")
    bibliography.create(entry, user)
    return entry


@pytest.fixture
def two_alias_entry(bibliography, user: User) -> dict:
    entry = BibliographyEntryFactory.build(
        id="RY0001",
        title="Two aliases",
        aliases=[ALIAS_A, ALIAS_B],
        citationKey=CITATION_KEY,
    )
    bibliography.create(entry, user)
    return entry


def stored(database, id_: str) -> dict:
    document = database["bibliography"].find_one({"_id": id_})
    assert document is not None
    return document


@pytest.mark.parametrize(
    "field,empty_value",
    [
        ("aliases", []),
        ("citationKey", ""),
        ("deprecated", False),
        ("redirectTo", None),
    ],
)
def test_empty_server_owned_value_against_no_stored_state_is_accepted(
    field, empty_value, client, database, plain_entry
):
    result = post_entry(client, {**plain_entry, "title": "Edited", field: empty_value})

    assert result.status == falcon.HTTP_NO_CONTENT
    document = stored(database, ENTRY_ID)
    assert document["title"] == "Edited"
    assert field not in document


def test_all_empty_server_owned_values_at_once_are_accepted(
    client, database, plain_entry
):
    body = {
        **plain_entry,
        "title": "Edited",
        "aliases": [],
        "citationKey": "",
        "deprecated": False,
        "redirectTo": None,
    }

    result = post_entry(client, body)

    assert result.status == falcon.HTTP_NO_CONTENT
    document = stored(database, ENTRY_ID)
    assert document["title"] == "Edited"
    assert not any(
        key in document
        for key in ("aliases", "citationKey", "deprecated", "redirectTo")
    )


def test_reordered_aliases_are_not_a_conflict(client, database, two_alias_entry):
    fetched = client.simulate_get(f"/bibliography/{two_alias_entry['id']}").json

    result = post_entry(
        client, {**fetched, "title": "Edited", "aliases": [ALIAS_B, ALIAS_A]}
    )

    assert result.status == falcon.HTTP_NO_CONTENT
    document = stored(database, two_alias_entry["id"])
    assert document["title"] == "Edited"
    assert document["aliases"] == [ALIAS_A, ALIAS_B]


def test_a_different_value_for_an_absent_field_is_still_a_conflict(
    client, database, plain_entry
):
    result = post_entry(client, {**plain_entry, "citationKey": "invented1999Key"})

    assert result.status == falcon.HTTP_CONFLICT
    assert "citationKey" in result.text
    assert "citationKey" not in stored(database, ENTRY_ID)


def test_deprecating_a_live_entry_through_metadata_is_still_a_conflict(
    client, database, plain_entry
):
    body = {**plain_entry, "deprecated": True, "redirectTo": "rla_9_388"}

    result = post_entry(client, body)

    assert result.status == falcon.HTTP_CONFLICT
    document = stored(database, ENTRY_ID)
    assert "deprecated" not in document
    assert "redirectTo" not in document
