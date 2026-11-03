import base64
import uuid
from contextlib import contextmanager
from typing import Iterator

import falcon
import pytest
from Cryptodome.PublicKey import RSA
from attr.exceptions import FrozenInstanceError
from pymongo import MongoClient

import ebl.app
import ebl.context
from ebl.ebl_ai_client import EblAiClient
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.application.transliteration_update_factory import (
    TransliterationUpdateFactory,
)
from ebl.transliteration.application.transliteration_query_factory import (
    TransliterationQueryFactory,
)

MONGODB_URI = "mongodb://unused-in-tests"


@pytest.fixture
def bootstrap_environment(
    monkeypatch: pytest.MonkeyPatch, mongo_client: MongoClient
) -> Iterator[None]:
    database_name = f"ebltest_{uuid.uuid4().hex[:8]}"
    public_key = RSA.generate(2048).publickey().export_key()
    monkeypatch.setenv("AUTH0_PEM", base64.b64encode(public_key).decode())
    monkeypatch.setenv("AUTH0_AUDIENCE", "test-audience")
    monkeypatch.setenv("AUTH0_ISSUER", "https://test.auth0.com/")
    monkeypatch.setenv("EBL_AI_API", "http://localhost:8001")
    monkeypatch.setenv("MONGODB_URI", MONGODB_URI)
    monkeypatch.setenv("MONGODB_DB", database_name)
    monkeypatch.setenv("SENTRY_DSN", "https://test@sentry.io/test")
    monkeypatch.setenv("SENTRY_ENVIRONMENT", "test")

    def client_for(uri: str) -> MongoClient:
        assert uri == MONGODB_URI
        return mongo_client

    monkeypatch.setattr(ebl.app, "MongoClient", client_for)
    yield
    mongo_client.drop_database(database_name)


def noop_sentry_init(*_args: object, **_kwargs: object) -> None:
    return None


@pytest.mark.usefixtures("bootstrap_environment")
def test_get_app_bootstraps(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ebl.app.sentry_sdk, "init", noop_sentry_init)

    app = ebl.app.get_app()

    assert isinstance(app, falcon.App)


@pytest.mark.usefixtures("bootstrap_environment")
def test_create_context_helpers() -> None:
    context = ebl.app.create_context()

    assert isinstance(context, ebl.context.Context)
    assert isinstance(context.get_fragment_updater(), FragmentUpdater)
    assert isinstance(
        context.get_transliteration_update_factory(), TransliterationUpdateFactory
    )
    assert isinstance(
        context.get_transliteration_query_factory(), TransliterationQueryFactory
    )

    frozen_attribute = "ebl_ai_client"
    with pytest.raises(FrozenInstanceError):
        setattr(context, frozen_attribute, EblAiClient("http://localhost:8001"))


@pytest.mark.usefixtures("bootstrap_environment")
def test_create_context_bootstraps_cache_indexes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"cache": 0}

    def cache_create_indexes(_self):
        calls["cache"] += 1

    monkeypatch.setattr(
        ebl.app.MongoCacheRepository,
        "create_indexes",
        cache_create_indexes,
    )

    ebl.app.create_context()

    assert calls["cache"] == 1


@pytest.mark.usefixtures("bootstrap_environment")
def test_create_app_bootstraps_bibliography_annotations_and_afo_indexes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"bibliography": 0, "reconcile": 0, "annotations": 0, "afo": 0}

    def bibliography_create_indexes(_self):
        calls["bibliography"] += 1

    def annotations_create_indexes(_self):
        calls["annotations"] += 1

    def bibliography_reconcile(_self, _now, limit=100):
        calls["reconcile"] += limit

    def afo_create_indexes(_self):
        calls["afo"] += 1

    monkeypatch.setattr(
        ebl.app.MongoBibliographyRepository,
        "create_indexes",
        bibliography_create_indexes,
    )
    monkeypatch.setattr(
        ebl.app.MongoAnnotationsRepository,
        "create_indexes",
        annotations_create_indexes,
    )
    monkeypatch.setattr(
        ebl.app.MongoBibliographyRepository,
        "reconcile_lookup_reservations",
        bibliography_reconcile,
    )
    monkeypatch.setattr(
        ebl.app.MongoAfoRegisterRepository,
        "create_indexes",
        afo_create_indexes,
    )

    context = ebl.app.create_context()
    ebl.app.create_app(context)

    assert calls["bibliography"] == 1
    assert calls["reconcile"] == 100
    assert calls["annotations"] == 1
    assert calls["afo"] == 1


class RecordingScope:
    user: object = None


def test_set_sentry_user_sets_the_scope_user(monkeypatch: pytest.MonkeyPatch) -> None:
    scope = RecordingScope()

    @contextmanager
    def configure_scope() -> Iterator[RecordingScope]:
        yield scope

    monkeypatch.setattr(ebl.app, "configure_scope", configure_scope)

    ebl.app.set_sentry_user("auth0|reader")

    assert scope.user == {"id": "auth0|reader"}
