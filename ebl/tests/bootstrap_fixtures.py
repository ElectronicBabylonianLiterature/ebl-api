import base64
import uuid
from typing import Iterator

import pytest
from Cryptodome.PublicKey import RSA
from pymongo import MongoClient

import ebl.app

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
