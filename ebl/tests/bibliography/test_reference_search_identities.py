import pytest

from ebl.bibliography.application.partner_identity import create_partner_alias
from ebl.bibliography.application.reference_documents import resolved_document
from ebl.bibliography.application.reference_search import (
    equivalent_reference_identities,
)
from ebl.bibliography.application.reference_search_identities import (
    ReferenceSearchIdentities,
    identities_of,
    requested_identities,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory


def test_identities_of_keeps_each_identity_type_separate():
    entry = {
        "id": "CANONICAL",
        "citationKey": "citation",
        "aliases": [{"value": "Legacy Alias", "normalizedValue": "legacy-alias"}],
    }

    assert identities_of(entry) == ReferenceSearchIdentities(
        bibliography_ids=("CANONICAL",),
        citation_keys=("citation",),
        alias_values=("Legacy Alias",),
        normalized_alias_values=("legacy-alias",),
    )


@pytest.mark.parametrize("id_", ["CANONICAL", "citation", "Legacy Alias"])
def test_stored_requested_identity_adds_nothing(id_):
    entry = {
        "id": "CANONICAL",
        "citationKey": "citation",
        "aliases": [{"value": "Legacy Alias", "normalizedValue": "legacy-alias"}],
    }

    assert requested_identities(id_, entry) == ReferenceSearchIdentities()


def test_normalized_spelling_is_searched_as_alias_value(bibliography_repository):
    bibliography_repository.create(
        BibliographyEntryFactory.build(
            id="CANONICAL", aliases=[create_partner_alias("UBHD-1718224")]
        )
    )

    identities = equivalent_reference_identities(
        "UBHD 1718224", bibliography_repository
    )

    assert identities.bibliography_ids == ("CANONICAL",)
    assert identities.alias_values == ("UBHD 1718224", "UBHD-1718224")
    assert identities.unresolved_reference_ids == ()


def test_unknown_identity_is_kept_as_unresolved(bibliography_repository):
    assert equivalent_reference_identities(
        "UNKNOWN", bibliography_repository
    ) == ReferenceSearchIdentities(unresolved_reference_ids=("UNKNOWN",))


def test_stored_reference_values_merge_fields_without_duplicates():
    identities = ReferenceSearchIdentities(
        bibliography_ids=("A",), alias_values=("x", "A")
    )

    assert identities.stored_reference_values() == ("A", "x")


@pytest.mark.parametrize("current_id", [None, 7])
def test_tombstone_without_string_id_is_not_resolved(current_id):
    document = {"id": current_id, "deprecated": True}

    assert resolved_document(document, {}) is None


def test_tombstone_without_redirect_target_resolves_to_itself():
    document = {"id": "OLD", "deprecated": True}

    assert resolved_document(document, {}) == document
