from typing import Mapping

import pytest

from pymongo.database import Database

from ebl.corpus.application.corpus import Corpus, CorpusDependencies
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.ebl_ai_client import EblAiClient
from ebl.fragmentarium.application.annotations_service import AnnotationsService
from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.application.fragment_matcher import FragmentMatcher
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.application.fragmentarium import Fragmentarium
from ebl.fragmentarium.infrastructure.mongo_fragment_repository import (
    MongoFragmentRepository,
)
from ebl.fragmentarium.infrastructure.mongo_findspot_repository import (
    MongoFindspotRepository,
)
from ebl.tests.fixtures.fixture_resolution import resolve_fixtures
from ebl.tests.factories.archaeology import FindspotFactory, FINDSPOT_COUNT


@pytest.fixture
def text_repository(database: Database, seeded_provenance_service):
    return MongoTextRepository(database, seeded_provenance_service)


CORPUS_DEPENDENCY_FIXTURES: Mapping[str, str] = {
    "repository": "text_repository",
    "bibliography": "bibliography",
    "changelog": "changelog",
    "sign_repository": "sign_repository",
    "parallel_line_injector": "parallel_line_injector",
    "provenance_service": "seeded_provenance_service",
}


FRAGMENT_FINDER_FIXTURES: Mapping[str, str] = {
    "bibliography": "bibliography",
    "repository": "fragment_repository",
    "dictionary": "dictionary",
    "photos": "photo_repository",
    "folios": "file_repository",
    "thumbnails": "thumbnail_repository",
    "parallel_injector": "parallel_line_injector",
}


@pytest.fixture
def corpus_dependencies(request: pytest.FixtureRequest) -> CorpusDependencies:
    return CorpusDependencies(**resolve_fixtures(request, CORPUS_DEPENDENCY_FIXTURES))


@pytest.fixture
def corpus(corpus_dependencies: CorpusDependencies) -> Corpus:
    return Corpus(corpus_dependencies)


@pytest.fixture
def fragment_repository(database, seeded_provenance_service):
    return MongoFragmentRepository(database, seeded_provenance_service)


@pytest.fixture
def findspot_repository(database, seeded_provenance_service):
    return MongoFindspotRepository(database, seeded_provenance_service)


@pytest.fixture
def findspots():
    return FindspotFactory.build_batch(FINDSPOT_COUNT)


@pytest.fixture
def fragmentarium(fragment_repository):
    return Fragmentarium(fragment_repository)


@pytest.fixture
def fragment_finder(request: pytest.FixtureRequest) -> FragmentFinder:
    return FragmentFinder(**resolve_fixtures(request, FRAGMENT_FINDER_FIXTURES))


@pytest.fixture
def fragment_matcher(fragment_repository):
    return FragmentMatcher(fragment_repository)


@pytest.fixture
def fragment_updater(
    fragment_repository,
    changelog,
    bibliography,
    photo_repository,
    parallel_line_injector,
):
    return FragmentUpdater(
        fragment_repository,
        changelog,
        bibliography,
        photo_repository,
        parallel_line_injector,
    )


@pytest.fixture
def annotations_service(
    annotations_repository,
    photo_repository,
    changelog,
    fragment_repository,
    cropped_sign_images_repository,
):
    return AnnotationsService(
        EblAiClient(""),
        annotations_repository,
        photo_repository,
        changelog,
        fragment_repository,
        photo_repository,
        cropped_sign_images_repository,
    )
