import pytest
from ebl.transliteration.domain.museum_number import MuseumNumber

from ebl.tests.media.test_media_management_uploads import (
    MediaTestUser,
    client,
    upload,
    if_match,
)


@pytest.mark.parametrize("fragment,expected", [("K.1", 403), ("K.2", 403)])
def test_readers_cannot_upload(management_runtime, fragment, expected):
    assert (
        upload(
            client(management_runtime, user=MediaTestUser(contributor=False)),
            fragment=fragment,
        ).status_code
        == expected
    )


def test_contributor_inaccessible_fragment(management_runtime):
    assert upload(client(management_runtime), fragment="K.2").status_code == 403
    assert upload(client(management_runtime), fragment="K.404").status_code == 404


def test_contributor_and_cross_fragment_permissions(management_runtime):
    owner = client(management_runtime)
    other = client(management_runtime, user=MediaTestUser(actor="auth0|other"))
    manager = client(management_runtime, user=MediaTestUser(manager=True))
    item = upload(owner).json["media"][0]
    path = f"/media/{item['id']}"
    assert other.simulate_get("/media?fragment=K.1&view=management").json == {
        "media": []
    }
    assert other.simulate_get(path + "/file?fragment=K.1").status_code == 404
    assert (
        other.simulate_patch(
            path + "?fragment=K.1", json={"caption": "Stolen"}
        ).status_code
        == 403
    )
    assert (
        owner.simulate_post(path + "/publish?fragment=K.1", json={}).status_code == 403
    )
    assert owner.simulate_delete(path + "?fragment=K.1").status_code == 403
    assert (
        owner.simulate_patch(
            path + "?fragment=K.1", json={"rightsStatement": "Changed"}
        ).status_code
        == 403
    )
    assert (
        owner.simulate_patch(path + "?fragment=K.1", json={"caption": "Edited"}).json[
            "media"
        ][0]["caption"]
        == "Edited"
    )
    assert (
        manager.simulate_post(path + "/primary?fragment=K.1", json={}).status_code
        == 409
    )
    assert (
        manager.simulate_post(path + "/publish?fragment=K.3", json={}).status_code
        == 404
    )
    assert (
        manager.simulate_patch(
            path + "?fragment=K.3", json={"caption": "Wrong"}
        ).status_code
        == 404
    )
    assert (
        manager.simulate_post(
            path + "/reject?fragment=K.1",
            json={"reason": "No permission evidence"},
            headers=if_match(1),
        ).status_code
        == 200
    )
    assert (
        owner.simulate_get("/media?fragment=K.1&view=management").json["media"][0][
            "reviewReason"
        ]
        == "No permission evidence"
    )
    assert (
        owner.simulate_patch(
            path + "?fragment=K.1", json={"caption": "Edited again"}
        ).status_code
        == 403
    )
    assert management_runtime.service.list_fragment_media(MuseumNumber.of("K.1")) == ()


def test_manager_only_scope_can_upload_then_explicitly_publish_own_submission(
    management_runtime,
):
    api = client(
        management_runtime,
        user=MediaTestUser(actor="auth0|manager", manager=True, contributor=False),
    )
    response = upload(api)
    assert response.status_code == 201
    item = response.json["media"][0]
    assert item["publicationStatus"] == "PENDING_REVIEW"
    number = MuseumNumber.of("K.1")
    assert management_runtime.service.find_media_by_fragments((number,))[number] == ()
    published = api.simulate_post(
        f"/media/{item['id']}/publish?fragment=K.1",
        json={},
        headers=if_match(item["revision"]),
    )
    assert published.status_code == 200
    assert published.json["media"][0]["reviewerId"] == "auth0|manager"
    assert (
        len(management_runtime.service.find_media_by_fragments((number,))[number]) == 1
    )
