import dataclasses
from itertools import chain
from typing import Callable, List

import attr
import falcon
import pytest
from falcon import testing
from pymongo.database import Database

import ebl.app
import ebl.context
from ebl.bibliography.application.bibliography import Bibliography
from ebl.cache.infrastructure.mongo_cache_repository import COLLECTION
from ebl.corpus.application.chapter_edit_writer import ChapterEditWriter
from ebl.corpus.application.corpus import CorpusDependencies
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.tests.corpus.chapter_edit_support import (
    CHAPTER_EDIT_KINDS,
    ChapterEdit,
    ChapterEditKind,
)
from ebl.tests.corpus.line_alignment_errors import INVALID_ALIGNMENTS
from ebl.tests.corpus.line_annotation_kind import AnnotationKind, InvalidAnnotation
from ebl.tests.corpus.line_annotation_kinds import ANNOTATION_KINDS
from ebl.tests.corpus.line_annotation_support import create_annotation_chapter
from ebl.tests.corpus.line_lemmatization_errors import INVALID_LEMMATIZATIONS
from ebl.tests.corpus.line_move_support import (
    create_extent_chapter,
    create_move_chapter,
)
from ebl.tests.corpus.lines_edit_support import (
    count_chapter_changelog_entries,
    find_stored_chapter,
)
from ebl.tests.corpus.reference_save_support import (
    ChapterCopies,
    ReferenceChapterEditWriter,
    ReferenceTextRepository,
)
from ebl.tests.corpus.support import (
    ANY_USER,
    allow_references,
    allow_signs,
    simulate_get,
)
from ebl.tests.corpus.word_instances_support import create_instances_chapter
from ebl.tests.factories.corpus import TextFactory
from ebl.provenance.application.provenance_service import ProvenanceService
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


@pytest.fixture
def store_text(text_repository: MongoTextRepository) -> Callable[[Chapter], Chapter]:
    def store(chapter: Chapter) -> Chapter:
        text_repository.create(
            TextFactory.build(
                genre=chapter.text_id.genre,
                category=chapter.text_id.category,
                index=chapter.text_id.index,
            )
        )
        return chapter

    return store


@pytest.fixture
def writer(corpus_dependencies: CorpusDependencies) -> ChapterEditWriter:
    return ChapterEditWriter(corpus_dependencies)


@pytest.fixture
def reference_repository(
    database: Database, seeded_provenance_service: ProvenanceService
) -> ReferenceTextRepository:
    return ReferenceTextRepository(database, seeded_provenance_service)


@pytest.fixture
def reference_writer(
    corpus_dependencies: CorpusDependencies,
    reference_repository: ReferenceTextRepository,
) -> ChapterEditWriter:
    return ReferenceChapterEditWriter(
        dataclasses.replace(corpus_dependencies, repository=reference_repository)
    )


@pytest.fixture
def reference_client(
    context: ebl.context.Context, reference_repository: ReferenceTextRepository
) -> testing.TestClient:
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(
            "ebl.corpus.web.bootstrap.ChapterEditWriter", ReferenceChapterEditWriter
        )
        api = ebl.app.create_app(
            attr.evolve(context, text_repository=reference_repository)
        )
    return testing.TestClient(api)


@pytest.fixture
def copies(
    database: Database,
    text_repository: MongoTextRepository,
    reference_repository: ReferenceTextRepository,
) -> ChapterCopies:
    return ChapterCopies(database, text_repository, reference_repository)


@pytest.fixture
def move_chapter(store_editable_chapter: Callable[[Chapter], Chapter]) -> Chapter:
    return store_editable_chapter(create_move_chapter())


@pytest.fixture
def extent_chapter(store_editable_chapter: Callable[[Chapter], Chapter]) -> Chapter:
    return store_editable_chapter(create_extent_chapter())


@pytest.fixture
def annotation_chapter(store_editable_chapter: Callable[[Chapter], Chapter]) -> Chapter:
    return store_editable_chapter(create_annotation_chapter())


@pytest.fixture
def instances_chapter(store_editable_chapter: Callable[[Chapter], Chapter]) -> Chapter:
    return store_editable_chapter(create_instances_chapter())


def create_unchanged_assertion(
    database: Database, chapter: Chapter
) -> Callable[[], None]:
    stored_chapter = find_stored_chapter(database, chapter)

    def assert_unchanged() -> None:
        assert find_stored_chapter(database, chapter) == stored_chapter
        assert count_chapter_changelog_entries(database) == 0

    return assert_unchanged


@pytest.fixture
def assert_nothing_saved(
    database: Database, annotation_chapter: Chapter
) -> Callable[[], None]:
    return create_unchanged_assertion(database, annotation_chapter)


@pytest.fixture
def assert_instances_unchanged(
    database: Database, instances_chapter: Chapter
) -> Callable[[], None]:
    return create_unchanged_assertion(database, instances_chapter)


@pytest.fixture(params=ANNOTATION_KINDS, ids=lambda kind: kind.name)
def annotation_kind(request: pytest.FixtureRequest) -> AnnotationKind:
    return request.param


@pytest.fixture(
    params=tuple(chain(INVALID_ALIGNMENTS, INVALID_LEMMATIZATIONS)),
    ids=lambda invalid: invalid.name,
)
def invalid_annotation(request: pytest.FixtureRequest) -> InvalidAnnotation:
    return request.param


@pytest.fixture(params=CHAPTER_EDIT_KINDS, ids=lambda edit_kind: edit_kind.suffix)
def edit_kind(request: pytest.FixtureRequest) -> ChapterEditKind:
    return request.param


@pytest.fixture
def save_sibling_without_revision(
    writer: ChapterEditWriter, text_repository: MongoTextRepository
) -> Callable[[Chapter, ChapterEdit], Chapter]:
    def save(chapter: Chapter, edit: ChapterEdit) -> Chapter:
        sibling = attr.evolve(chapter, name=f"{chapter.name} sibling")
        text_repository.create_chapter(sibling)
        return attr.evolve(
            edit.save(writer, sibling.id_, None, ANY_USER).chapter, name=chapter.name
        )

    return save
