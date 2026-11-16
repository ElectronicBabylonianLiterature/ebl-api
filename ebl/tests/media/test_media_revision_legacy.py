from ebl.tests.media.factories import photo_media, stored_media
from ebl.tests.media.test_media_management_uploads import (
    client,
    if_match,
)

from ebl.tests.media.test_media_revision_guard import _manager, _listed


def test_legacy_document_without_revision_reads_as_zero(
    management_runtime, media_database
):
    legacy = photo_media()
    management_runtime.management.repository.create(stored_media(legacy))
    media_database.media.update_one(
        {"_id": str(legacy.id)}, {"$unset": {"revision": ""}}
    )
    assert "revision" not in media_database.media.find_one({"_id": str(legacy.id)})
    manager = _manager(management_runtime)

    assert _listed(manager, str(legacy.id))["revision"] == 0
    response = manager.simulate_patch(
        f"/media/{legacy.id}?fragment=K.1",
        json={"caption": "Annotated"},
        headers=if_match(0),
    )
    assert response.status_code == 200, response.text
    assert response.json["media"][0]["revision"] == 1
    assert media_database.media.find_one({"_id": str(legacy.id)})["revision"] == 1


def test_contributors_do_not_see_revisions_of_legacy_items(management_runtime):
    legacy = photo_media()
    management_runtime.management.repository.create(stored_media(legacy))
    item = _listed(client(management_runtime), str(legacy.id))
    assert "revision" not in item
