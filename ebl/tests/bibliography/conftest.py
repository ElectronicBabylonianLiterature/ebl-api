import pytest

from ebl.tests.factories.bibliography import BibliographyEntryFactory


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
