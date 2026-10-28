from typing import Optional, Sequence, cast

import pytest

from marshmallow import EXCLUDE
from pymongo.database import Database

from ebl.bibliography.application.bibliography import Bibliography
from ebl.bibliography.application.serialization import create_object_entry
from ebl.bibliography.infrastructure.bibliography import MongoBibliographyRepository
from ebl.cache.infrastructure.mongo_cache_repository import MongoCacheRepository
from ebl.dictionary.application.dictionary_service import Dictionary
from ebl.dictionary.infrastructure.word_repository import MongoWordRepository
from ebl.ebl_ai_client import EblAiClient
from ebl.fragmentarium.application.transliteration_update_factory import (
    TransliterationUpdateFactory,
)
from ebl.fragmentarium.infrastructure.cropped_sign_images_repository import (
    MongoCroppedSignImagesRepository,
)
from ebl.fragmentarium.infrastructure.mongo_annotations_repository import (
    MongoAnnotationsRepository,
)
from ebl.lemmatization.infrastrcuture.mongo_suggestions_finder import (
    MongoLemmaRepository,
)
from ebl.signs.infrastructure.mongo_sign_repository import (
    MongoSignRepository,
    SignSchema,
)
from ebl.transliteration.application.parallel_line_injector import ParallelLineInjector
from ebl.transliteration.domain.sign import (
    Sign,
)
from ebl.transliteration.infrastructure.mongo_parallel_repository import (
    MongoParallelRepository,
)
from ebl.afo_register.infrastructure.mongo_afo_register_repository import (
    MongoAfoRegisterRepository,
)
from ebl.dossiers.infrastructure.mongo_dossiers_repository import (
    MongoDossiersRepository,
)
from ebl.realia.infrastructure.mongo_realia_repository import MongoRealiaRepository
from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.tests.factories.provenance import build_provenance_records
from ebl.provenance.infrastructure.mongo_provenance_repository import (
    MongoProvenanceRepository,
)


class TestWordRepository(MongoWordRepository):
    # Mongomock does not support $substrCP so we need to
    # stub the methods using it.
    def query_by_lemma_prefix(self, query: str) -> Sequence:
        return [self._collection.find_one({})]


@pytest.fixture
def word_repository(database):
    return TestWordRepository(database)


@pytest.fixture
def dictionary(word_repository, changelog):
    return Dictionary(word_repository, changelog)


@pytest.fixture
def cropped_sign_images_repository(database):
    return MongoCroppedSignImagesRepository(database)


@pytest.fixture
def mongo_cache_repository(database):
    return MongoCacheRepository(database)


@pytest.fixture
def ebl_ai_client():
    return EblAiClient("http://localhost:8001")


class TestBibliographyRepository(MongoBibliographyRepository):
    # Mongomock does not support $substrCP so we need to
    # stub the methods using it.
    def query_by_author_year_and_title(
        self, author: Optional[str], year: Optional[int], title: Optional[str]
    ) -> Sequence[dict]:
        return [create_object_entry(self._collection.find_one({}))]


class TestSignRepository(MongoSignRepository):
    # Mongomock does not support $let in lookup so we need to
    # stub the methods using it.
    # https://github.com/mongomock/mongomock/issues/536

    def search_composite_signs(self, reading: str, sub_index: int) -> Sequence[Sign]:
        return [
            cast(Sign, SignSchema(unknown=EXCLUDE).load(self._collection.find_one({})))
        ]


@pytest.fixture
def bibliography_repository(database):
    return TestBibliographyRepository(database)


@pytest.fixture
def bibliography(bibliography_repository, changelog):
    return Bibliography(bibliography_repository, changelog)


@pytest.fixture
def sign_repository(database):
    return TestSignRepository(database)


@pytest.fixture
def transliteration_factory(sign_repository):
    return TransliterationUpdateFactory(sign_repository)


@pytest.fixture
def parallel_repository(database: Database) -> MongoParallelRepository:
    return MongoParallelRepository(database)


@pytest.fixture
def parallel_line_injector(
    parallel_repository: MongoParallelRepository,
) -> ParallelLineInjector:
    return ParallelLineInjector(parallel_repository)


@pytest.fixture
def afo_register_repository(database):
    return MongoAfoRegisterRepository(database)


@pytest.fixture
def annotations_repository(database):
    return MongoAnnotationsRepository(database)


@pytest.fixture
def lemma_repository(database):
    return MongoLemmaRepository(database)


@pytest.fixture
def dossiers_repository(database, seeded_provenance_service):
    return MongoDossiersRepository(database, seeded_provenance_service)


@pytest.fixture
def realia_repository(database):
    return MongoRealiaRepository(database)


@pytest.fixture
def provenance_repository(database):
    return MongoProvenanceRepository(database)


@pytest.fixture
def provenance_service(provenance_repository):
    return ProvenanceService(provenance_repository)


@pytest.fixture
def seeded_provenance_service(provenance_repository):
    for record in build_provenance_records():
        provenance_repository.create(record)
    return ProvenanceService(provenance_repository)
