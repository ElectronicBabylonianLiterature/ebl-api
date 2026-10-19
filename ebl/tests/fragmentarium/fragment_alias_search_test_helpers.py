import pytest

from ebl.bibliography.application.partner_identity import create_partner_alias
from ebl.tests.factories.bibliography import BibliographyEntryFactory


@pytest.fixture
def equivalent_bibliography(bibliography_repository):
    entries = [
        BibliographyEntryFactory.build(
            id="UBHD-1718224",
            aliases=[create_partner_alias("RN1971axx"), create_partner_alias("LS276")],
            citationKey="Rawlinson1870",
        ),
        BibliographyEntryFactory.build(
            id="DEPRECATED", deprecated=True, redirectTo="UBHD-1718224"
        ),
        BibliographyEntryFactory.build(
            id="OLDER", deprecated=True, redirectTo="DEPRECATED"
        ),
    ]
    for entry in entries:
        bibliography_repository.create(entry)
    return entries
