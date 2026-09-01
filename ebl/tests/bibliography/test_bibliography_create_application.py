"""The create invariant holds below HTTP, not only in the route schema."""

import pytest

from ebl.bibliography.application.partner_identity import create_partner_alias
from ebl.errors import DataError
from ebl.tests.factories.bibliography import BibliographyEntryFactory

SERVER_OWNED_VALUES = {
    "aliases": [{"value": "client-alias", "normalizedValue": "client-alias"}],
    "citationKey": "clientChosen",
    "deprecated": True,
    "redirectTo": "OTHER-ID",
}


def entry(**overrides):
    return BibliographyEntryFactory.build(**{"id": "APP-1", **overrides})


def test_ordinary_metadata_creation_succeeds(bibliography, user):
    bibliography_entry = entry()

    assert bibliography.create_metadata(bibliography_entry, user) == "APP-1"
    assert bibliography.find("APP-1") == bibliography_entry


@pytest.mark.parametrize("field", sorted(SERVER_OWNED_VALUES))
def test_ordinary_metadata_creation_refuses_server_owned_state(
    field, bibliography, user, database
):
    with pytest.raises(DataError, match=field):
        bibliography.create_metadata(entry(**{field: SERVER_OWNED_VALUES[field]}), user)

    assert database["bibliography"].count_documents({}) == 0


def test_trusted_creation_still_builds_server_owned_state(bibliography, user):
    """`create` is the trusted path partner and identity code rely on."""
    alias = create_partner_alias("dossin1967archives")
    bibliography_entry = entry(aliases=[alias], citationKey="dossin1967La")

    bibliography.create(bibliography_entry, user)

    assert bibliography.find("dossin1967archives")["id"] == "APP-1"
    assert bibliography.find("dossin1967La")["id"] == "APP-1"


def test_trusted_creation_still_builds_tombstones(bibliography, user):
    bibliography.create(BibliographyEntryFactory.build(id="CANONICAL"), user)

    bibliography.create(entry(deprecated=True, redirectTo="CANONICAL"), user)

    assert bibliography.find("APP-1")["id"] == "CANONICAL"


def test_partner_creation_still_constructs_its_identity(bibliography, user):
    partner_entry = {"type": "book", "id": "partner-local-1", "title": "Partner"}

    assert bibliography.create_partner_entry(partner_entry, user) is None

    created = bibliography.find(partner_entry["id"])
    assert created["id"].startswith("Q")
    assert created["aliases"] == [create_partner_alias("partner-local-1")]
