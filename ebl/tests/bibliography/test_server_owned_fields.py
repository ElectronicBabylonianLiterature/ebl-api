import pytest

from ebl.bibliography.application.server_owned_fields import (
    preserve_server_owned_fields,
    stored_server_owned_fields,
    strip_server_owned_fields,
)

ALIASES = [{"value": "legacy-id", "normalizedValue": "legacy-id"}]
STORED = {
    "id": "Q30000024",
    "type": "book",
    "title": "Stored title",
    "aliases": ALIASES,
    "citationKey": "stored-key",
}


@pytest.mark.parametrize(
    "field", ["aliases", "citationKey", "deprecated", "redirectTo"]
)
def test_strip_removes_every_server_owned_field(field):
    entry = {"id": "Q30000024", "type": "book", field: "value"}

    assert strip_server_owned_fields(entry) == {"id": "Q30000024", "type": "book"}


def test_strip_keeps_metadata():
    assert strip_server_owned_fields(STORED) == {
        "id": "Q30000024",
        "type": "book",
        "title": "Stored title",
    }


def test_stored_server_owned_fields_collects_present_fields():
    assert stored_server_owned_fields(STORED) == {
        "aliases": ALIASES,
        "citationKey": "stored-key",
    }


def test_stored_server_owned_fields_omits_absent_fields():
    assert stored_server_owned_fields({"id": "RN1", "type": "book"}) == {}


def test_preserve_restores_omitted_fields():
    entry = {"id": "Q30000024", "type": "book", "title": "Corrected"}

    assert preserve_server_owned_fields(entry, STORED) == {
        "id": "Q30000024",
        "type": "book",
        "title": "Corrected",
        "aliases": ALIASES,
        "citationKey": "stored-key",
    }


def test_preserve_overrides_submitted_server_owned_fields():
    entry = {
        "id": "Q30000024",
        "type": "book",
        "aliases": [{"value": "attacker", "normalizedValue": "attacker"}],
        "citationKey": "attacker-key",
    }

    preserved_entry = preserve_server_owned_fields(entry, STORED)

    assert preserved_entry["aliases"] == ALIASES
    assert preserved_entry["citationKey"] == "stored-key"


def test_preserve_drops_submitted_fields_absent_from_stored():
    entry = {
        "id": "RN1",
        "type": "book",
        "deprecated": True,
        "redirectTo": "other-record",
    }

    assert preserve_server_owned_fields(entry, {"id": "RN1", "type": "book"}) == {
        "id": "RN1",
        "type": "book",
    }


def test_preserve_keeps_stored_tombstone_fields():
    stored_entry: dict[str, object] = {
        "id": "RN2001",
        "type": "book",
        "deprecated": True,
        "redirectTo": "rla_9_388",
    }
    entry = {"id": "RN2001", "type": "book", "title": "Corrected"}

    preserved_entry = preserve_server_owned_fields(entry, stored_entry)

    assert preserved_entry["deprecated"] is True
    assert preserved_entry["redirectTo"] == "rla_9_388"
