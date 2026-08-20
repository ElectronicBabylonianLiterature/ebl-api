"""`POST /bibliography` is an ordinary create, not an identity endpoint."""

import falcon
import pytest

from ebl.tests.bibliography.identity_preservation_test_helpers import reservations
from ebl.tests.factories.bibliography import BibliographyEntryFactory

SERVER_OWNED_VALUES = {
    "aliases": [{"value": "client-alias", "normalizedValue": "client-alias"}],
    "citationKey": "clientChosen",
    "deprecated": True,
    "redirectTo": "OTHER-ID",
}
NEW_ID = "NEW-ENTRY"


def create(client, entry):
    return client.simulate_post("/bibliography", json=entry)


def new_entry(**overrides):
    return BibliographyEntryFactory.build(**{"id": NEW_ID, **overrides})


def test_a_plain_metadata_create_succeeds(client):
    entry = new_entry()

    result = create(client, entry)

    assert result.status == falcon.HTTP_CREATED
    assert client.simulate_get(f"/bibliography/{NEW_ID}").json == entry


def test_the_client_supplied_canonical_id_is_kept(client):
    entry = new_entry(id="rla_9_388")

    create(client, entry)

    assert client.simulate_get("/bibliography/rla_9_388").json["id"] == "rla_9_388"


def test_rich_metadata_is_accepted(client):
    entry = new_entry(
        abstract="An abstract.",
        keyword="lexical",
        editor=[{"given": "E.", "family": "Editor"}],
        **{"original-date": {"date-parts": [[1899]]}},
    )

    result = create(client, entry)

    assert result.status == falcon.HTTP_CREATED
    assert client.simulate_get(f"/bibliography/{NEW_ID}").json == entry


@pytest.mark.parametrize("field", sorted(SERVER_OWNED_VALUES))
def test_a_server_owned_field_is_rejected(field, client):
    result = create(client, new_entry(**{field: SERVER_OWNED_VALUES[field]}))

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert field in result.text
    assert "/identity" in result.text


def test_every_server_owned_field_is_named_at_once(client):
    result = create(client, new_entry(**SERVER_OWNED_VALUES))

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    for field in SERVER_OWNED_VALUES:
        assert field in result.text


def test_a_tombstone_cannot_be_created(client, bibliography, user):
    bibliography.create(BibliographyEntryFactory.build(id="CANONICAL"), user)

    result = create(client, new_entry(deprecated=True, redirectTo="CANONICAL"))

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert (
        client.simulate_get(f"/bibliography/{NEW_ID}").status == falcon.HTTP_NOT_FOUND
    )


def test_an_alias_cannot_be_created(client):
    alias = {"value": "clientAlias", "normalizedValue": "clientalias"}

    result = create(client, new_entry(aliases=[alias]))

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert client.simulate_get("/bibliography/clientAlias").status == (
        falcon.HTTP_NOT_FOUND
    )


def test_a_client_citation_key_cannot_be_created(client):
    result = create(client, new_entry(citationKey="clientChosen"))

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert client.simulate_get("/bibliography/clientChosen").status == (
        falcon.HTTP_NOT_FOUND
    )


def test_an_explicit_redirect_to_null_is_rejected(client):
    """`redirectTo: null` and absent are distinct in storage, so neither the
    ambiguous shape nor the field may originate from a client."""
    result = create(client, new_entry(redirectTo=None))

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert "redirectTo" in result.text


@pytest.mark.parametrize(
    "field,value",
    [("aliases", "not-a-list"), ("citationKey", 7), ("deprecated", "yes")],
)
def test_a_malformed_server_owned_field_is_still_rejected(field, value, client):
    result = create(client, new_entry(**{field: value}))

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert field in result.text


def test_an_unknown_property_is_rejected_by_the_schema(client):
    result = create(client, new_entry(notACslField="x"))

    assert result.status == falcon.HTTP_BAD_REQUEST


def test_a_non_object_body_is_rejected_by_the_schema(client):
    """The guard inspects `req.media`, so a non-object body must fall through
    to the schema rather than fail while looking for server-owned fields."""
    result = client.simulate_post("/bibliography", json=[new_entry()])

    assert result.status == falcon.HTTP_BAD_REQUEST


def test_a_rejected_create_persists_nothing(client, database):
    create(client, new_entry(**SERVER_OWNED_VALUES))

    assert database["bibliography"].count_documents({}) == 0
    assert reservations(database) == {}
