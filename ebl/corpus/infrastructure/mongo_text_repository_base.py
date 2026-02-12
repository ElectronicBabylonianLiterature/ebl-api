from pymongo.database import Database
from ebl.corpus.application.text_repository import TextRepository
from ebl.corpus.domain.chapter import ChapterId
from ebl.corpus.domain.text import TextId
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


class MongoTextRepositoryBase(TextRepository):
    def __init__(self, database: Database, provenance_service):
        self._texts = MongoCollection(database, TEXTS_COLLECTION)
        self._chapters = MongoCollection(database, CHAPTERS_COLLECTION)
        self._provenance_service = provenance_service
