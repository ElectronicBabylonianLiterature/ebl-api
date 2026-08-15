import pytest

from ebl.bibliography.application.bibliography_repository import (
    LookupValueReservationError,
)
from ebl.bibliography.application.partner_bibliography import PartnerBibliography
from ebl.errors import NotFoundError
from ebl.tests.factories.bibliography import BibliographyEntryFactory


class FakeRepository:
    def __init__(self):
        self.calls = 0

    def list_all_bibliography(self):
        self.calls += 1
        return ["Q30000000"][: self.calls - 1]

    def lookup_value_is_reserved(self, _value):
        return False


class FakeBibliography:
    def __init__(self, errors=()):
        self._errors = list(errors)
        self.created_entries = []

    def create(self, entry, _user):
        if self._errors:
            raise self._errors.pop(0)
        self.created_entries.append(dict(entry))
        return entry["id"]

    def update(self, _entry, _user):
        raise NotImplementedError

    def find(self, id_):
        raise NotFoundError(f"{id_} not found")

    def find_duplicate_candidates(self, _entry, limit=10):
        return {"decision": "unique", "candidates": []}


def test_create_entry_retries_canonical_id_after_reservation_conflict(user):
    bibliography = FakeBibliography([LookupValueReservationError("Q30000000")])
    partner_bibliography = PartnerBibliography(bibliography, FakeRepository())
    entry = BibliographyEntryFactory.build(id="partner-id")

    partner_bibliography.create_entry(entry, user)

    assert entry["id"] == "Q30000001"
    assert bibliography.created_entries == [entry]


def test_create_entry_regenerates_citation_key_after_reservation_conflict(user):
    bibliography = FakeBibliography(
        [LookupValueReservationError("miccadei2002Synergistic")]
    )
    partner_bibliography = PartnerBibliography(bibliography, FakeRepository())
    entry = BibliographyEntryFactory.build(id="partner-id")

    partner_bibliography.create_entry(entry, user)

    assert entry["citationKey"] == "miccadei2002Synergistic-2"
    assert bibliography.created_entries == [entry]


def test_create_entry_raises_unrelated_lookup_reservation_conflict(user):
    bibliography = FakeBibliography([LookupValueReservationError("other-value")])
    partner_bibliography = PartnerBibliography(bibliography, FakeRepository())
    entry = BibliographyEntryFactory.build(id="partner-id")

    with pytest.raises(LookupValueReservationError):
        partner_bibliography.create_entry(entry, user)

    assert entry["id"] == "partner-id"
    assert bibliography.created_entries == []


def test_update_citation_key_removes_key_when_regeneration_has_no_source_data():
    partner_bibliography = PartnerBibliography(FakeBibliography(), FakeRepository())
    entry = {"id": "Q30000000", "type": "book", "citationKey": "oldKey"}

    partner_bibliography._update_citation_key(entry, [])

    assert "citationKey" not in entry
