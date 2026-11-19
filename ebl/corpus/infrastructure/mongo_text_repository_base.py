from ebl.bibliography.infrastructure.bibliography import MongoBibliographyRepository
from pymongo.database import Database
from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.corpus.application.text_repository import TextRepository
from ebl.corpus.domain.chapter import ChapterId
from ebl.corpus.domain.text import TextId
from ebl.corpus.domain.chapter_revision import LEGACY_REVISION
from ebl.errors import NotFoundError
from ebl.mongo_collection import MongoCollection
from ebl.transliteration.infrastructure.collections import (
    CHAPTERS_COLLECTION,
    TEXTS_COLLECTION,
)


def text_not_found(id_: TextId) -> Exception:
    return NotFoundError(f"Text {id_} not found.")


def chapter_not_found(id_: ChapterId) -> Exception:
    return NotFoundError(f"Chapter {id_} not found.")


def line_not_found(id_: ChapterId, number: int) -> Exception:
    return NotFoundError(f"Chapter {id_} line {number} not found.")


REVISION_FIELD = "_cacheRevision"


def revision_query(revision: str) -> dict:
    return {REVISION_FIELD: None if revision == LEGACY_REVISION else revision}


class MongoTextRepositoryBase(TextRepository):
    def __init__(
        self, database: Database, provenance_service: ProvenanceService
    ) -> None:
        self._texts = MongoCollection(database, TEXTS_COLLECTION)
        self._chapters = MongoCollection(database, CHAPTERS_COLLECTION)
        self._provenance_service = provenance_service
        self._bibliography_repository = MongoBibliographyRepository(database)
