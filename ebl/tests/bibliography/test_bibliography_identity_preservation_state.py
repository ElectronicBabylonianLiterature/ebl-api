import json

import pydash
import pytest
from falcon import testing

from ebl.bibliography.application.bibliography_repository import LookupValueInUseError
from ebl.bibliography.application.lookup_reservation import LookupReservationState
from ebl.tests.factories.bibliography import BibliographyEntryFactory

RESERVATIONS = "bibliography_lookup_reservations"
PARTNER_ALIAS = {
    "value": "dossin1967archives",
    "normalizedValue": "dossin1967archives",
    "type": "partner_id",
    "source": "partner_request",
    "status": "redirect",
}
CITATION_KEY = "dossin1967La"


@pytest.fixture
def aliased_entry(bibliography, user):
    entry = BibliographyEntryFactory.build(
        id="Q30000024",
        title="Old title",
        aliases=[PARTNER_ALIAS],
        citationKey=CITATION_KEY,
    )
    bibliography.create(entry, user)
    return entry


@pytest.fixture
def deprecated_entry(bibliography, user):
    canonical_entry = BibliographyEntryFactory.build(id="rla_9_388", title="Canonical")
    bibliography.create(canonical_entry, user)
    entry = BibliographyEntryFactory.build(
        id="RN2001", title="Loser", deprecated=True, redirectTo="rla_9_388"
    )
    bibliography.create(entry, user)
    return entry


def reservations(database) -> dict:
    return {document["_id"]: document for document in database[RESERVATIONS].find({})}


def metadata_only_payload(entry: dict) -> dict:
    return pydash.omit(
        {**entry, "title": "Corrected title"},
        "aliases",
        "citationKey",
        "deprecated",
        "redirectTo",
    )


def post_entry(client, entry: dict) -> testing.Result:
    return client.simulate_post(f"/bibliography/{entry['id']}", body=json.dumps(entry))


def test_metadata_update_keeps_every_reservation(client, database, aliased_entry):
    before = reservations(database)

    post_entry(client, metadata_only_payload(aliased_entry))

    assert set(reservations(database)) == set(before)
    assert set(before) == {aliased_entry["id"], CITATION_KEY, PARTNER_ALIAS["value"]}


def test_metadata_update_does_not_retire_reservations(client, database, aliased_entry):
    post_entry(client, metadata_only_payload(aliased_entry))

    assert [document["state"] for document in reservations(database).values()] == [
        LookupReservationState.COMMITTED.value
    ] * 3


def test_metadata_update_keeps_reservation_owners(client, database, aliased_entry):
    owners_before = {
        value: document["owner"] for value, document in reservations(database).items()
    }

    post_entry(client, metadata_only_payload(aliased_entry))

    assert {
        value: document["owner"] for value, document in reservations(database).items()
    } == owners_before


def test_metadata_update_does_not_add_reservations(client, database, aliased_entry):
    payload = {
        **metadata_only_payload(aliased_entry),
        "citationKey": "brand-new-key",
        "aliases": [{"value": "brand-new", "normalizedValue": "brand-new"}],
    }

    post_entry(client, payload)

    assert "brand-new-key" not in reservations(database)
    assert "brand-new" not in reservations(database)


def test_deprecated_record_update_is_rejected(bibliography, user, deprecated_entry):
    with pytest.raises(LookupValueInUseError):
        bibliography.update(
            {**metadata_only_payload(deprecated_entry), "id": "RN2001"}, user
        )


def test_rejected_deprecated_update_keeps_tombstone(
    bibliography, user, database, deprecated_entry
):
    with pytest.raises(LookupValueInUseError):
        bibliography.update(
            {**metadata_only_payload(deprecated_entry), "id": "RN2001"}, user
        )
    stored_entry = database["bibliography"].find_one({"_id": "RN2001"})

    assert stored_entry["deprecated"] is True
    assert stored_entry["redirectTo"] == "rla_9_388"


def test_rejected_deprecated_update_keeps_redirect_working(
    bibliography, user, deprecated_entry
):
    with pytest.raises(LookupValueInUseError):
        bibliography.update(
            {**metadata_only_payload(deprecated_entry), "id": "RN2001"}, user
        )

    assert bibliography.find("RN2001")["id"] == "rla_9_388"


def test_deprecated_record_update_cannot_clear_tombstone_fields(
    bibliography, user, database, deprecated_entry
):
    with pytest.raises(LookupValueInUseError):
        bibliography.update(
            {
                **metadata_only_payload(deprecated_entry),
                "id": "RN2001",
                "deprecated": False,
            },
            user,
        )
    stored_entry = database["bibliography"].find_one({"_id": "RN2001"})

    assert stored_entry["deprecated"] is True
    assert stored_entry["redirectTo"] == "rla_9_388"
