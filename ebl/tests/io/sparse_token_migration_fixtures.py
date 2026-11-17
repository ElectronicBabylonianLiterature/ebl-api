from typing import Any, Dict, cast

from pymongo.database import Database

from ebl.corpus.application.schemas import ChapterSchema
from ebl.corpus.domain.chapter import Chapter
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.tests.factories.corpus import ChapterFactory
from ebl.tests.factories.fragment import LemmatizedFragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber

FRAGMENT: Fragment = LemmatizedFragmentFactory.build(number=MuseumNumber("X", "1"))
CHAPTER: Chapter = ChapterFactory.build()


def full_fragment_document(
    fragment: Fragment, provenance_service: ProvenanceService
) -> Dict[str, Any]:
    schema = FragmentSchema(
        exclude=["joins"], context={"provenance_service": provenance_service}
    )
    return {"_id": str(fragment.number), **cast(dict, schema.dump(fragment))}


def full_chapter_document(chapter: Chapter) -> Dict[str, Any]:
    return cast(dict, ChapterSchema().dump(chapter))


def insert_full_documents(
    database: Database, provenance_service: ProvenanceService
) -> None:
    database.fragments.insert_one(full_fragment_document(FRAGMENT, provenance_service))
    database.chapters.insert_one(full_chapter_document(CHAPTER))


def stored_fragment(database: Database) -> Dict[str, Any]:
    return cast(dict, database.fragments.find_one({"_id": str(FRAGMENT.number)}))


def stored_chapter(database: Database) -> Dict[str, Any]:
    return cast(dict, database.chapters.find_one({}))
