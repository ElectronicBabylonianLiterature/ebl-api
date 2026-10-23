import os
from collections.abc import Callable, Iterator
from urllib.parse import quote

import attr
import pytest
from falcon import testing
from falcon_auth import NoneAuthBackend
from pymongo import MongoClient, monitoring
from pymongo.database import Database

from ebl.app import create_app
from ebl.context import Context
from ebl.fragmentarium.infrastructure.mongo_fragment_repository import (
    MongoFragmentRepository,
)
from ebl.media.application.media_stored import StoredMedia
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.media.web.helpers import body, get
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.infrastructure.queries import query_number_is
from ebl.users.domain.user import Guest


class FragmentReadRecorder(monitoring.CommandListener):
    def __init__(self) -> None:
        self.commands: list[dict] = []

    def started(self, event: monitoring.CommandStartedEvent) -> None:
        self.commands.append(dict(event.command))

    def succeeded(self, event: monitoring.CommandSucceededEvent) -> None:
        pass

    def failed(self, event: monitoring.CommandFailedEvent) -> None:
        pass


@pytest.fixture
def observed_media_context(
    database: Database, media_context: Context
) -> Iterator[tuple[Context, FragmentReadRecorder]]:
    recorder = FragmentReadRecorder()
    client: MongoClient[dict] = MongoClient(
        os.environ["MONGODB_URI"], event_listeners=[recorder]
    )
    with client:
        repository = MongoFragmentRepository(
            client[database.name], media_context.provenance_service
        )
        yield attr.evolve(media_context, fragment_repository=repository), recorder


def prepare_scope_case(database: Database, scenario: str) -> tuple[str, int, bool]:
    number = "A/B.1"
    status = 200
    guest = True
    if scenario == "missing-scopes":
        database.fragments.update_one(
            {"_id": number}, {"$unset": {"authorizedScopes": 1}}
        )
    elif scenario in {"restricted", "allowed", "legacy-scope", "wrong-scope"}:
        scopes = [
            "read:COPENHAGEN-fragments"
            if scenario == "wrong-scope"
            else "read:CAIC-fragments"
        ]
        if scenario == "legacy-scope":
            scopes = ["read:CAIC"]
        database.fragments.update_one(
            {"_id": number}, {"$set": {"authorizedScopes": scopes}}
        )
        guest = scenario == "restricted"
        status = 403 if scenario in {"restricted", "wrong-scope"} else 200
    elif scenario in {"false-scopes", "null-scopes", "unknown-scope"}:
        value = {
            "false-scopes": False,
            "null-scopes": None,
            "unknown-scope": ["read:UNKNOWN-fragments"],
        }[scenario]
        database.fragments.update_one(
            {"_id": number}, {"$set": {"authorizedScopes": value}}
        )
        status = 500
    elif scenario == "unknown-fragment":
        number, status = "K.999", 404
    elif scenario == "unrelated-fragment":
        number, status = "K.2", 404
    return number, status, guest


@pytest.mark.parametrize(
    "suffix",
    ["", "/file", "/display", "/thumbnail/small"],
    ids=["list", "file", "display", "thumbnail"],
)
@pytest.mark.parametrize(
    "scenario",
    [
        "public",
        "missing-scopes",
        "restricted",
        "allowed",
        "legacy-scope",
        "wrong-scope",
        "false-scopes",
        "null-scopes",
        "unknown-scope",
        "unknown-fragment",
        "unrelated-fragment",
    ],
)
def test_media_authorization_uses_only_projected_scope_read(
    database: Database,
    observed_media_context: tuple[Context, FragmentReadRecorder],
    create_media: Callable[..., StoredMedia],
    scenario: str,
    suffix: str,
) -> None:
    stored = create_media("A/B.1")
    context, recorder = observed_media_context
    context.fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of("K.2"), references=())
    )
    number, status, guest = prepare_scope_case(database, scenario)
    if guest:
        context = attr.evolve(context, auth_backend=NoneAuthBackend(Guest))
    client = testing.TestClient(create_app(context))
    path = f"/media/{stored.media.id}{suffix}" if suffix else "/media"
    recorder.commands.clear()

    response = get(client, f"{path}?fragment={quote(number, safe='')}")

    expected_status = 200 if scenario == "unrelated-fragment" and not suffix else status
    assert response.status_code == expected_status
    if scenario == "unknown-fragment":
        assert body(response)["description"] == "Fragment K.999 not found."
    if scenario == "unrelated-fragment" and not suffix:
        assert body(response) == {"media": []}
    assert [
        (command.get("find"), command.get("aggregate")) for command in recorder.commands
    ] == [("fragments", None)]
    [command] = recorder.commands
    assert command["filter"] == query_number_is(MuseumNumber.of(number))
    assert command["projection"] == {"authorizedScopes": True, "_id": False}
