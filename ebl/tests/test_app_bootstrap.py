import base64

import falcon
import pytest
from Cryptodome.PublicKey import RSA
from attr.exceptions import FrozenInstanceError
from pymongo_inmemory import MongoClient as InMemoryMongoClient

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


def configure_environment(monkeypatch: pytest.MonkeyPatch, public_key: bytes) -> None:
    monkeypatch.setenv("AUTH0_PEM", base64.b64encode(public_key).decode())
    monkeypatch.setenv("AUTH0_AUDIENCE", "test-audience")
    monkeypatch.setenv("AUTH0_ISSUER", "https://test.auth0.com/")
    monkeypatch.setenv("EBL_AI_API", "http://localhost:8001")
    monkeypatch.setenv("MONGODB_URI", "mongodb://localhost:27017")
    monkeypatch.setenv("MONGODB_DB", "ebltest")
    monkeypatch.setenv("SENTRY_DSN", "https://test@sentry.io/test")
    monkeypatch.setenv("SENTRY_ENVIRONMENT", "test")
    monkeypatch.setenv("PYMONGOIM__OPERATING_SYSTEM", "ubuntu")
    monkeypatch.setenv("PYMONGOIM__OS_VERSION", "20")


def noop_sentry_init(*_args: object, **_kwargs: object) -> None:
    return None


def test_get_app_bootstraps(monkeypatch: pytest.MonkeyPatch) -> None:
    key = RSA.generate(2048)
    configure_environment(monkeypatch, key.publickey().export_key())
    monkeypatch.setattr(ebl.app, "MongoClient", InMemoryMongoClient)
    monkeypatch.setattr(ebl.app.sentry_sdk, "init", noop_sentry_init)

    app = ebl.app.get_app()

    assert isinstance(app, falcon.App)


def test_create_context_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    key = RSA.generate(2048)
    configure_environment(monkeypatch, key.publickey().export_key())
    monkeypatch.setattr(ebl.app, "MongoClient", InMemoryMongoClient)

    context = ebl.app.create_context()

    assert isinstance(context, ebl.context.Context)
    assert isinstance(context.get_fragment_updater(), FragmentUpdater)
    assert isinstance(
        context.get_transliteration_update_factory(), TransliterationUpdateFactory
    )
    assert isinstance(
        context.get_transliteration_query_factory(), TransliterationQueryFactory
    )

    with pytest.raises(FrozenInstanceError):
        context.ebl_ai_client = EblAiClient("http://localhost:8001")
