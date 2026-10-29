from typing import Callable, cast

import attr
import pytest
from falcon import testing
from falcon_auth import NoneAuthBackend
from falcon_caching import Cache

import ebl.app
from ebl.context import Context
from ebl.sumerian_dictionary.domain.sumerian_word import SumerianWord
from ebl.sumerian_dictionary.infrastructure.mongo_sumerian_word_repository import (
    MongoSumerianWordRepository,
)
from ebl.sumerian_dictionary.infrastructure.sumerian_word_schemas import (
    SumerianWordDocumentSchema,
)
from ebl.users.infrastructure.auth0 import Auth0User

InsertWords = Callable[..., None]


@pytest.fixture
def insert_words(
    sumerian_word_repository: MongoSumerianWordRepository,
) -> InsertWords:
    def insert(*words: SumerianWord) -> None:
        sumerian_word_repository._collection.insert_many(
            [cast(dict, SumerianWordDocumentSchema().dump(word)) for word in words]
        )

    return insert


@pytest.fixture
def sumerian_reader() -> Auth0User:
    return Auth0User(
        {"scope": "read:sumerian-words"},
        lambda: {"name": "reader@example.com", "https://ebabylon.org/eblName": "R"},
    )


def _client(context: Context, user: Auth0User) -> testing.TestClient:
    reader_context = attr.evolve(context, auth_backend=NoneAuthBackend(lambda: user))
    return testing.TestClient(ebl.app.create_app(reader_context))


@pytest.fixture
def reader_client(context: Context, sumerian_reader: Auth0User) -> testing.TestClient:
    return _client(context, sumerian_reader)


@pytest.fixture
def cached_reader_client(
    context: Context, sumerian_reader: Auth0User
) -> testing.TestClient:
    cached_context = attr.evolve(context, cache=Cache(config={"CACHE_TYPE": "simple"}))
    return _client(cached_context, sumerian_reader)
