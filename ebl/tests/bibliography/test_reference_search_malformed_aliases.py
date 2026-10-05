import pytest

from ebl.bibliography.application.lookup_identity import bibliography_lookup_values
from ebl.bibliography.application.reference_search import (
    equivalent_reference_identities,
)
from ebl.bibliography.application.reference_search_identities import (
    ReferenceSearchIdentities,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory


@pytest.mark.parametrize("aliases", [None, 7, "alias", {"value": "alias"}])
def test_lookup_values_ignore_malformed_alias_containers(aliases):
    assert bibliography_lookup_values(
        {"id": "CANONICAL", "citationKey": "citation", "aliases": aliases}
    ) == ["CANONICAL", "citation"]


def test_lookup_values_retain_valid_aliases_and_skip_malformed_members():
    assert bibliography_lookup_values(
        {
            "id": "CANONICAL",
            "aliases": [
                None,
                "bad",
                {"value": "Legacy Alias", "normalizedValue": "legacy-alias"},
                {"value": 7, "normalizedValue": None},
            ],
        }
    ) == ["CANONICAL", "Legacy Alias", "legacy-alias"]


@pytest.mark.parametrize("malformed_id", ["CANONICAL", "OLD"])
@pytest.mark.parametrize("aliases", [None, 7, "alias", {"value": "alias"}])
def test_reference_search_ignores_malformed_persisted_aliases(
    bibliography_repository, malformed_id, aliases
):
    for entry in (
        BibliographyEntryFactory.build(id="CANONICAL"),
        BibliographyEntryFactory.build(
            id="OLD", deprecated=True, redirectTo="CANONICAL"
        ),
    ):
        if entry["id"] == malformed_id:
            entry["aliases"] = aliases
        bibliography_repository.create(entry)

    assert equivalent_reference_identities(
        "CANONICAL", bibliography_repository
    ) == ReferenceSearchIdentities(bibliography_ids=("CANONICAL", "OLD"))
