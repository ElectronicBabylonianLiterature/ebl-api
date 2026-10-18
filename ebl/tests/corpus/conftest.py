from typing import Callable

import falcon
import pytest


@pytest.fixture
def assert_served_without_caching(
    client, database, monkeypatch
) -> Callable[[str], None]:
    def assert_served(url: str) -> None:
        monkeypatch.setattr(
            "ebl.cache.infrastructure.mongo_cache_repository.MAX_BSON_SIZE", 0
        )
        uncached_result = client.simulate_get(url)
        assert uncached_result.status == falcon.HTTP_OK
        assert database["cache"].count_documents({}) == 0

        monkeypatch.undo()
        cached_result = client.simulate_get(url)
        assert database["cache"].count_documents({}) == 1
        assert uncached_result.json == cached_result.json

    return assert_served
