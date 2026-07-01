"""Test that bibliography routes handle special (non-ASCII) characters in IDs."""
import json
import urllib.parse

import falcon

from ebl.tests.factories.bibliography import BibliographyEntryFactory


def test_get_entry_with_special_char_in_id(client, bibliography, user):
    """Bibliography entry with special char Ê in ID should be findable."""
    entry = BibliographyEntryFactory.build(
        id="Young2023\u00ca",  # Young2023Ê
    )
    bibliography.create(entry, user)

    # GET by unencoded ID
    get_result = client.simulate_get("/bibliography/Young2023\u00ca")
    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == entry

    # GET by URL-encoded ID (as browsers send it)
    encoded_id = urllib.parse.quote("Young2023\u00ca")
    get_result2 = client.simulate_get(f"/bibliography/{encoded_id}")
    assert get_result2.status == falcon.HTTP_OK
    assert get_result2.json == entry


def test_update_entry_with_special_char_in_id(client, bibliography, user):
    """Bibliography entry with special char Ê in ID should be updatable."""
    entry = BibliographyEntryFactory.build(
        id="Young2023\u00ca",  # Young2023Ê
    )
    bibliography.create(entry, user)

    updated_entry = {**entry, "title": "Updated Title"}
    body = json.dumps(updated_entry)

    # UPDATE by URL-encoded ID
    encoded_id = urllib.parse.quote("Young2023\u00ca")
    put_result = client.simulate_post(f"/bibliography/{encoded_id}", body=body)
    assert put_result.status == falcon.HTTP_NO_CONTENT

    # Verify the update
    get_result = client.simulate_get(f"/bibliography/{encoded_id}")
    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == updated_entry
