from typing import Callable

import falcon
import pytest
from falcon import testing
from pymongo.database import Database

from ebl.cache.infrastructure.mongo_cache_repository import COLLECTION
from ebl.tests.corpus.support import simulate_get


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
