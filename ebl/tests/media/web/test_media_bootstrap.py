import pytest
from Cryptodome.PublicKey import RSA
from pymongo.database import Database
from sentry_sdk import isolation_scope

import ebl.app
from ebl.tests.test_app_bootstrap import configure_environment


@pytest.mark.parametrize("enabled", ["true", "TRUE"])
def test_environment_enables_media_without_creating_media_collections(
    database: Database, monkeypatch: pytest.MonkeyPatch, enabled: str
) -> None:
    configure_environment(monkeypatch, RSA.generate(2048).public_key().export_key())
    monkeypatch.setenv("MONGODB_DB", database.name)
    monkeypatch.setenv("MEDIA_API_ENABLED", enabled)
    monkeypatch.setattr(ebl.app, "MongoClient", lambda _: database.client)
    context = ebl.app.create_context()
    assert context.media is not None
    assert not any(
        name.startswith("media") for name in database.list_collection_names()
    )


@pytest.mark.parametrize("enabled", ["false", "", "invalid"])
def test_environment_keeps_media_disabled(
    database: Database, monkeypatch: pytest.MonkeyPatch, enabled: str
) -> None:
    configure_environment(monkeypatch, RSA.generate(2048).public_key().export_key())
    monkeypatch.setenv("MONGODB_DB", database.name)
    monkeypatch.setenv("MEDIA_API_ENABLED", enabled)
    monkeypatch.setattr(ebl.app, "MongoClient", lambda _: database.client)
    assert ebl.app.create_context().media is None


def test_authentication_callback_sets_isolated_sentry_user() -> None:
    with isolation_scope() as scope:
        ebl.app.set_sentry_user("media-reader")
        event = scope.apply_to_event({}, {})
        assert event is not None
        assert event.get("user") == {"id": "media-reader"}
