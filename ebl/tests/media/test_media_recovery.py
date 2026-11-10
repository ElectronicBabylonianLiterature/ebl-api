from ebl.tests.media.test_media_management_uploads import MediaTestUser
import pytest

from ebl.media.infrastructure.media_recovery import recover_media
from ebl.tests.media.test_media_management_uploads import client, upload


def test_offline_recovery_requires_quiescence(management_runtime, media_database):
    with pytest.raises(ValueError, match="drained"):
        recover_media(media_database, apply=True)


def test_tombstone_recovery_is_explicit_and_preserves_other_files(
    management_runtime, media_database
):
    api = client(management_runtime, user=MediaTestUser(manager=True))
    first = upload(api).json["media"][0]
    second = upload(api).json["media"][0]
    assert api.simulate_delete(f"/media/{first['id']}?fragment=K.1").status_code == 204
    assert len(recover_media(media_database)) == 1
    assert media_database["media.files"].count_documents({}) == 10
    recover_media(media_database, apply=True, quiescent=True)
    assert media_database["media.files"].count_documents({}) == 5
    assert (
        api.simulate_get(second["representations"]["original"]["url"]).status_code
        == 200
    )
    assert media_database.media.find_one({"_id": first["id"]}) is None


def test_failed_commit_is_quarantined_and_recoverable(
    management_runtime, media_database, monkeypatch
):
    repository = management_runtime.management.repository
    original_commit = repository.commit_upload

    def fail(*args, **kwargs):
        raise RuntimeError("Injected commit failure")

    monkeypatch.setattr(repository, "commit_upload", fail)
    assert upload(client(management_runtime)).status_code == 500
    assert media_database.media.count_documents({}) == 0
    assert media_database["media.files"].count_documents({}) == 5
    request = media_database.mediaUploadRequests.find_one({})
    assert request["state"] == "failed"
    assert len(request["stagedHandles"]) == 5
    assert recover_media(media_database)[0]["action"] == "recover-incomplete"
    recover_media(media_database, apply=True, quiescent=True)
    assert media_database["media.files"].count_documents({}) == 0
    monkeypatch.setattr(repository, "commit_upload", original_commit)
