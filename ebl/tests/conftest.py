import os
import uuid

import attr
import pytest

from falcon import testing
from falcon_auth import NoneAuthBackend
from falcon_caching import Cache
from pymongo import MongoClient

import ebl.app
from ebl.changelog import Changelog
from ebl.fragmentarium.application.annotations_service import AnnotationsService
from ebl.users.domain.user import Guest, User
from ebl.users.infrastructure.auth0 import Auth0User
from ebl.fragmentarium.web.annotations import AnnotationResource


@pytest.fixture(scope="session")
def mongo_client() -> MongoClient:
    if os.getenv("CI") == "true":
        return MongoClient(os.environ["MONGODB_URI"])
    else:
        os.environ.setdefault("PYMONGOIM__OPERATING_SYSTEM", "ubuntu")
        os.environ.setdefault("PYMONGOIM__OS_VERSION", "20")

        from pymongo_inmemory import MongoClient as InMemoryMongoClient

        return InMemoryMongoClient()


@pytest.fixture
def database(mongo_client: MongoClient):
    database = str(uuid.uuid4())
    yield mongo_client[database]
    mongo_client.drop_database(database)


@pytest.fixture
def changelog(database):
    return Changelog(database)


@pytest.fixture
def user() -> User:
    return Auth0User(
        {
            "scope": " ".join(
                [
                    "read:words",
                    "write:words",
                    "transliterate:fragments",
                    "lemmatize:fragments",
                    "annotate:fragments",
                    "read:CAIC-fragments",
                    "read:SIPPARLIBRARY-fragments",
                    "read:ITALIANNINEVEH-fragments",
                    "read:URUKLBU-fragments",
                    "read:WGL-folios",
                    "read:bibliography",
                    "check:bibliography_duplicates",
                    "export:bibliography",
                    "write:bibliography",
                    "read:texts",
                    "write:texts",
                    "create:texts",
                ]
            )
        },
        lambda: {
            "name": "test.user@example.com",
            "https://ebabylon.org/eblName": "User",
        },
    )


@pytest.fixture
def client(context):
    api = ebl.app.create_app(context)
    return testing.TestClient(api)


class EnsureAnnotationPost:
    def __init__(self, service: AnnotationsService) -> None:
        self._resource = AnnotationResource(service)

    def on_post(self, req, resp):
        return self._resource.on_post(req, resp, "K.123")


@pytest.fixture
def guest_client(context, annotations_service):
    api = ebl.app.create_app(attr.evolve(context, auth_backend=NoneAuthBackend(Guest)))
    api.add_route(
        "/fragments/K.123/annotations", EnsureAnnotationPost(annotations_service)
    )
    return testing.TestClient(api)


@pytest.fixture
def cached_client(context):
    api = ebl.app.create_app(
        attr.evolve(
            context,
            cache=Cache(config={"CACHE_TYPE": "simple"}),
        )
    )
    return testing.TestClient(api)
