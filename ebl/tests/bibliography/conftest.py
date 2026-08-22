import pytest

from ebl.tests.bibliography.identity_preservation_test_helpers import (
    CITATION_KEY,
    PARTNER_ALIAS,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory


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


@pytest.fixture
def saved_entry(bibliography, user):
    bibliography_entry = BibliographyEntryFactory.build()
    bibliography.create(bibliography_entry, user)
    return bibliography_entry


@pytest.fixture
def saved_entries(bibliography, user):
    number_of_entries = 5
    entries = [
        BibliographyEntryFactory.build(id=f"XY{i + 1:05}")
        for i in range(number_of_entries)
    ]

    for entry in entries:
        bibliography.create(entry, user)

    return entries
