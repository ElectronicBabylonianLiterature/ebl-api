from typing import Mapping

import pytest
from falcon_auth import NoneAuthBackend
from falcon_caching import Cache

import ebl.context
from ebl.cache.application.custom_cache import ChapterCache
from ebl.sumerian_dictionary.infrastructure.mongo_sumerian_word_repository import (
    MongoSumerianWordRepository,
)
from ebl.tests.fixtures.fixture_resolution import resolve_fixtures
from ebl.users.domain.user import User

CONTEXT_FIXTURES: Mapping[str, str] = {
    "ebl_ai_client": "ebl_ai_client",
    "cropped_sign_images_repository": "cropped_sign_images_repository",
    "word_repository": "word_repository",
    "sign_repository": "sign_repository",
    "public_file_repository": "file_repository",
    "photo_repository": "photo_repository",
    "folio_repository": "folio_repository",
    "thumbnail_repository": "thumbnail_repository",
    "fragment_repository": "fragment_repository",
    "text_repository": "text_repository",
    "changelog": "changelog",
    "bibliography_repository": "bibliography_repository",
    "provenance_repository": "provenance_repository",
    "provenance_service": "seeded_provenance_service",
    "annotations_repository": "annotations_repository",
    "lemma_repository": "lemma_repository",
    "afo_register_repository": "afo_register_repository",
    "dossiers_repository": "dossiers_repository",
    "findspot_repository": "findspot_repository",
    "realia_repository": "realia_repository",
    "sumerian_word_repository": "sumerian_word_repository",
    "parallel_line_injector": "parallel_line_injector",
}


@pytest.fixture
def sumerian_word_repository(database) -> MongoSumerianWordRepository:
    return MongoSumerianWordRepository(database)


@pytest.fixture
def context(
    request: pytest.FixtureRequest, user: User, mongo_cache_repository
) -> ebl.context.Context:
    return ebl.context.Context(
        auth_backend=NoneAuthBackend(lambda: user),
        cache=Cache({"CACHE_TYPE": "null"}),
        custom_cache=ChapterCache(mongo_cache_repository),
        **resolve_fixtures(request, CONTEXT_FIXTURES),
    )
