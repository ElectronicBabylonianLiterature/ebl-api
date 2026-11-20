from typing import Callable, List

import attr
import falcon
import pytest
from falcon import testing
from pymongo.database import Database

from ebl.bibliography.application.bibliography import Bibliography
from ebl.cache.infrastructure.mongo_cache_repository import COLLECTION
from ebl.corpus.application.corpus import Corpus
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.tests.corpus.chapter_edit_support import (
    CHAPTER_EDIT_KINDS,
    ChapterEdit,
    ChapterEditKind,
)
from ebl.tests.corpus.support import (
    ANY_USER,
    allow_references,
    allow_signs,
    simulate_get,
)
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


@pytest.fixture(params=CHAPTER_EDIT_KINDS, ids=lambda edit_kind: edit_kind.suffix)
def edit_kind(request: pytest.FixtureRequest) -> ChapterEditKind:
    return request.param


@pytest.fixture
def save_sibling_with_corpus(
    corpus: Corpus, text_repository: MongoTextRepository
) -> Callable[[Chapter, ChapterEdit], Chapter]:
    def save(chapter: Chapter, edit: ChapterEdit) -> Chapter:
        sibling = attr.evolve(chapter, name=f"{chapter.name} sibling")
        text_repository.create_chapter(sibling)
        return attr.evolve(
            edit.save_with_corpus(corpus, sibling.id_, ANY_USER), name=chapter.name
        )

    return save
