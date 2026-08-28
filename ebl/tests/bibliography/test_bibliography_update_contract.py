import json

import falcon
import pydash
import pytest

from ebl.tests.bibliography.identity_preservation_test_helpers import CITATION_KEY
from ebl.tests.factories.bibliography import BibliographyEntryFactory
from ebl.users.domain.user import User

LEGACY_KEY = "legacyOnlyField"


@pytest.fixture
def entry_with_legacy_key(bibliography, user: User, database) -> dict:
    entry = BibliographyEntryFactory.build(id="Q30000050", title="Legacy")
    bibliography.create(entry, user)
    database["bibliography"].update_one(
        {"_id": entry["id"]}, {"$set": {LEGACY_KEY: "keep-me"}}
    )
    return entry


def stored(database, id_: str) -> dict:
    document = database["bibliography"].find_one({"_id": id_})
    assert document is not None
    return document


def test_get_body_with_a_non_csl_key_round_trips_through_update(
    client, database, entry_with_legacy_key
):
    id_ = entry_with_legacy_key["id"]
    fetched = client.simulate_get(f"/bibliography/{id_}").json
    assert LEGACY_KEY in fetched

    result = client.simulate_post(f"/bibliography/{id_}", body=json.dumps(fetched))

    assert result.status == falcon.HTTP_NO_CONTENT
    assert stored(database, id_)[LEGACY_KEY] == "keep-me"


def test_update_edits_metadata_while_preserving_the_non_csl_key(
    client, database, entry_with_legacy_key
):
    id_ = entry_with_legacy_key["id"]
    fetched = client.simulate_get(f"/bibliography/{id_}").json

    result = client.simulate_post(
        f"/bibliography/{id_}", body=json.dumps({**fetched, "title": "Edited"})
    )

    assert result.status == falcon.HTTP_NO_CONTENT
    document = stored(database, id_)
    assert document["title"] == "Edited"
    assert document[LEGACY_KEY] == "keep-me"


def test_update_without_a_body_id_takes_the_id_from_the_url(
    client, database, saved_entry
):
    id_ = saved_entry["id"]
    body = pydash.omit({**saved_entry, "title": "URL id wins"}, "id")

    result = client.simulate_post(f"/bibliography/{id_}", body=json.dumps(body))

    assert result.status == falcon.HTTP_NO_CONTENT
    assert stored(database, id_)["title"] == "URL id wins"


def test_get_resolves_a_citation_key_that_update_does_not_address(
    client, aliased_entry
):
    get_result = client.simulate_get(f"/bibliography/{CITATION_KEY}")
    post_result = client.simulate_post(
        f"/bibliography/{CITATION_KEY}",
        body=json.dumps({**aliased_entry, "title": "Edited"}),
    )

    assert get_result.status == falcon.HTTP_OK
    assert post_result.status == falcon.HTTP_NOT_FOUND
