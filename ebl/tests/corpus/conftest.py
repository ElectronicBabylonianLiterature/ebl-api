from typing import Callable, List

import falcon
import pytest
from falcon import testing
from pymongo.database import Database

from ebl.bibliography.application.bibliography import Bibliography
from ebl.cache.infrastructure.mongo_cache_repository import COLLECTION
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.tests.corpus.support import allow_references, allow_signs, simulate_get
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.sign import Sign


@pytest.fixture
def assert_served_without_caching(
    client: testing.TestClient, database: Database, monkeypatch: pytest.MonkeyPatch
) -> Callable[[str], None]:
    def assert_served(url: str) -> None:
        with monkeypatch.context() as patch:
            patch.setattr(
                "ebl.cache.infrastructure.mongo_cache_repository.MAX_BSON_SIZE", 0
            )
            uncached_result = simulate_get(client, url)
        assert uncached_result.status == falcon.HTTP_OK
        assert database[COLLECTION].count_documents({}) == 0

        cached_result = simulate_get(client, url)
        assert database[COLLECTION].count_documents({}) == 1
        assert uncached_result.json == cached_result.json

    return assert_served


@pytest.fixture
def registered_sign_repository(
    sign_repository: SignRepository, signs: List[Sign]
) -> SignRepository:
    allow_signs(signs, sign_repository)

    return sign_repository


@pytest.fixture
def store_editable_chapter(
    text_repository: MongoTextRepository,
    bibliography: Bibliography,
    registered_sign_repository: SignRepository,
) -> Callable[[Chapter], Chapter]:
    def store(chapter: Chapter) -> Chapter:
        allow_references(chapter, bibliography)
        text_repository.create_chapter(chapter)
        return chapter

    return store
