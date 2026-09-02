"""Which record a metadata update is allowed to write to.

Reads follow identity and writes do not. `GET /bibliography/{id}` resolves a
citation key, an alias or a redirect and answers with the canonical entry, but
the matching `POST` refuses every identifier except the entry's own id, so an
edit can never land on a record the caller never looked at. The refusal names
the record to edit instead, which is the part that used to be a bare `404`.
"""

import falcon
import pytest

from ebl.bibliography.application.bibliography_repository import (
    BibliographyUpdateConflictError,
)
from ebl.tests.bibliography.identity_preservation_test_helpers import (
    CITATION_KEY,
    CORRECTED_TITLE,
    PARTNER_ALIAS,
    metadata_only_payload,
    post_entry,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory

NON_CANONICAL_IDENTIFIERS = [CITATION_KEY, PARTNER_ALIAS["value"]]


def payload_for(entry: dict, id_: str) -> dict:
    return {**metadata_only_payload(entry), "id": id_}


@pytest.mark.parametrize("identifier", NON_CANONICAL_IDENTIFIERS)
def test_update_through_a_citation_key_or_alias_is_refused(
    identifier, client, aliased_entry
):
    result = post_entry(client, payload_for(aliased_entry, identifier))

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize("identifier", NON_CANONICAL_IDENTIFIERS)
def test_refusal_names_the_record_to_edit_instead(identifier, client, aliased_entry):
    result = post_entry(client, payload_for(aliased_entry, identifier))

    assert aliased_entry["id"] in result.text


@pytest.mark.parametrize("identifier", NON_CANONICAL_IDENTIFIERS)
def test_a_refused_identifier_writes_nothing(
    identifier, client, bibliography, aliased_entry
):
    post_entry(client, payload_for(aliased_entry, identifier))
    stored_entry = bibliography.find(aliased_entry["id"])

    assert stored_entry["title"] == aliased_entry["title"]
    assert stored_entry["aliases"] == [PARTNER_ALIAS]
    assert stored_entry["citationKey"] == CITATION_KEY


def test_update_through_the_canonical_id_still_succeeds(
    client, bibliography, aliased_entry
):
    result = post_entry(client, metadata_only_payload(aliased_entry))

    assert result.status == falcon.HTTP_NO_CONTENT
    assert bibliography.find(aliased_entry["id"])["title"] == CORRECTED_TITLE


def test_update_through_a_deprecated_id_names_the_redirect_target(
    client, deprecated_entry
):
    result = post_entry(client, metadata_only_payload(deprecated_entry))

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert "is deprecated" in result.text
    assert "rla_9_388" in result.text


def test_an_identifier_that_resolves_to_nothing_is_still_not_found(client):
    entry = BibliographyEntryFactory.build()

    result = post_entry(client, entry)

    assert result.status == falcon.HTTP_NOT_FOUND


def test_a_direct_caller_supplying_stale_identity_fails_loudly(
    bibliography, user, aliased_entry
):
    """The trusted path no longer drops server-owned fields in silence.

    `Bibliography.update` used to ignore whatever identity a caller supplied,
    so a stale one produced a successful write that quietly kept the stored
    values. There is now one metadata editor and it reports the mismatch.
    """
    stale_entry = {**aliased_entry, "citationKey": "someoneElse1999Aa"}

    with pytest.raises(BibliographyUpdateConflictError) as conflict:
        bibliography.update_metadata(stale_entry, user)

    assert conflict.value.fields == ("citationKey",)
    assert bibliography.find(aliased_entry["id"])["citationKey"] == CITATION_KEY
