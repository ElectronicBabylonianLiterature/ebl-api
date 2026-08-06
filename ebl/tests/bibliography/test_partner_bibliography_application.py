import pytest

from ebl.bibliography.application.bibliography_repository import (
    LookupValueReservationError,
)
from ebl.bibliography.application.lookup_reservation import LookupReservationOperation
from ebl.bibliography.application.partner_bibliography import PartnerBibliography
from ebl.errors import DataError, DuplicateError, NotFoundError
from ebl.tests.factories.bibliography import BibliographyEntryFactory


class FakeRepository:
    def __init__(self, existing_ids=None, reserved_values=()):
        self._existing_ids = list(existing_ids or [])
        self._reserved_values = set(reserved_values)
        self.calls = 0
        self.released_entry_ids = []

    def list_all_bibliography(self):
        self.calls += 1
        return self._existing_ids[: self.calls - 1]

    def claim_lookup_values(self, _operation: LookupReservationOperation, values):
        for value in set(values):
            if value in self._reserved_values:
                raise LookupValueReservationError(value)

    def commit_lookup_values(self, _operation, _now):
        return None

    def release_pending_lookup_values(self, owner):
        self.released_entry_ids.append(owner)

    def retire_lookup_values(self, _entry_id, _values, _now):
        return None

    def lookup_value_is_reserved(self, value):
        return value in self._reserved_values

    def reconcile_lookup_reservations(self, _now, _limit=100):
        return 0


class FakeBibliography:
    def __init__(self, duplicate_creates=0, ambiguous_lookups=()):
        self._duplicate_creates = duplicate_creates
        self._ambiguous_lookups = set(ambiguous_lookups)
        self.created_entries = []

    def create(self, entry, _user):
        if self._duplicate_creates:
            self._duplicate_creates -= 1
            raise DuplicateError("duplicate id")
        self.created_entries.append(dict(entry))
        return entry["id"]

    def update(self, _entry, _user):
        raise NotImplementedError

    def find(self, id_):
        if id_ in self._ambiguous_lookups:
            raise DuplicateError("ambiguous")
        raise NotFoundError(f"{id_} not found")

    def find_duplicate_candidates(self, _entry, limit=10):
        return {"decision": "unique", "candidates": []}


def test_create_entry_retries_duplicate_canonical_ids(user):
    bibliography = FakeBibliography(duplicate_creates=1)
    repository = FakeRepository(existing_ids=["Q30000000"])
    partner_bibliography = PartnerBibliography(bibliography, repository)
    entry = BibliographyEntryFactory.build(id="partner-id")

    partner_bibliography.create_entry(entry, user)

    assert entry["id"] == "Q30000001"
    assert bibliography.created_entries[0]["id"] == "Q30000001"


def test_create_entry_retries_reserved_canonical_id(user):
    bibliography = FakeBibliography()
    repository = FakeRepository(reserved_values=["Q30000000"])
    partner_bibliography = PartnerBibliography(bibliography, repository)
    entry = BibliographyEntryFactory.build(id="partner-id")

    partner_bibliography.create_entry(entry, user)

    assert entry["id"] == "Q30000001"
    assert bibliography.created_entries[0]["id"] == "Q30000001"


def test_create_entry_uses_next_citation_key_when_base_reserved(user):
    bibliography = FakeBibliography()
    repository = FakeRepository(reserved_values=["miccadei2002Synergistic"])
    partner_bibliography = PartnerBibliography(bibliography, repository)
    entry = BibliographyEntryFactory.build(id="partner-id")

    partner_bibliography.create_entry(entry, user)

    assert entry["citationKey"] == "miccadei2002Synergistic-2"
    assert bibliography.created_entries[0]["citationKey"] == entry["citationKey"]


def test_create_entry_uses_third_citation_key_when_base_and_second_reserved(user):
    bibliography = FakeBibliography()
    repository = FakeRepository(
        reserved_values=["miccadei2002Synergistic", "miccadei2002Synergistic-2"]
    )
    partner_bibliography = PartnerBibliography(bibliography, repository)
    entry = BibliographyEntryFactory.build(id="partner-id")

    partner_bibliography.create_entry(entry, user)

    assert entry["citationKey"] == "miccadei2002Synergistic-3"


def test_create_entry_bounds_citation_key_generation(user):
    base_key = "miccadei2002Synergistic"
    reserved_values = [base_key, *(f"{base_key}-{suffix}" for suffix in range(2, 101))]
    bibliography = FakeBibliography()
    repository = FakeRepository(reserved_values=reserved_values)
    partner_bibliography = PartnerBibliography(bibliography, repository)
    entry = BibliographyEntryFactory.build(id="partner-id")

    with pytest.raises(
        DuplicateError, match="Unable to generate a unique citation key"
    ):
        partner_bibliography.create_entry(entry, user)

    assert bibliography.created_entries == []


def test_create_entry_rejects_reserved_alias_before_create(user):
    bibliography = FakeBibliography()
    repository = FakeRepository(reserved_values=["partner-id"])
    partner_bibliography = PartnerBibliography(bibliography, repository)
    entry = BibliographyEntryFactory.build(id="partner-id")

    with pytest.raises(DuplicateError, match="already in use"):
        partner_bibliography.create_entry(entry, user)

    assert bibliography.created_entries == []


def test_create_entry_raises_when_canonical_id_retries_are_exhausted(user):
    bibliography = FakeBibliography(duplicate_creates=5)
    partner_bibliography = PartnerBibliography(bibliography, FakeRepository())
    entry = BibliographyEntryFactory.build(id="partner-id")

    with pytest.raises(DuplicateError, match="Unable to generate"):
        partner_bibliography.create_entry(entry, user)

    assert entry["id"] == "partner-id"


def test_create_entry_rejects_ambiguous_partner_id_before_create(user):
    bibliography = FakeBibliography(ambiguous_lookups=["ambiguous-id"])
    partner_bibliography = PartnerBibliography(bibliography, FakeRepository())
    entry = BibliographyEntryFactory.build(id="ambiguous-id")

    with pytest.raises(DuplicateError, match="already in use"):
        partner_bibliography.create_entry(entry, user)

    assert bibliography.created_entries == []


def test_create_entry_converts_internal_schema_failure_to_data_error(user):
    partner_bibliography = PartnerBibliography(FakeBibliography(), FakeRepository())
    entry = BibliographyEntryFactory.build(id="partner-id", type="not-a-csl-type")

    with pytest.raises(DataError):
        partner_bibliography.create_entry(entry, user)
