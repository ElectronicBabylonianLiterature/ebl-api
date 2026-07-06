from ebl.bibliography.application.bibliography_repository import BibliographyRepository
from ebl.realia.domain.realia_entry import RealiaEntry
from ebl.realia.infrastructure.mongo_realia_repository import MongoRealiaRepository
from ebl.realia.infrastructure.realia_schemas import RealiaEntrySchema
from ebl.tests.factories.realia import RealiaEntryFactory


def insert_stored(realia_repository: MongoRealiaRepository, document: dict) -> None:
    realia_repository._realia_collection.insert_one(document)


def create_entry_with_bibliography(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
    entry: RealiaEntry,
) -> None:
    realia_repository._realia_collection.insert_one(RealiaEntrySchema().dump(entry))
    for reference in entry.references:
        if reference.document:
            bibliography_repository.create(reference.document)
    for reallexikon_entry in entry.reallexikon:
        if (
            reallexikon_entry.reference is not None
            and reallexikon_entry.reference.document
        ):
            bibliography_repository.create(reallexikon_entry.reference.document)


def insert_minimal(realia_repository: MongoRealiaRepository, identifier: str) -> None:
    entry = RealiaEntryFactory.build(
        id=identifier, related_terms=(), references=(), reallexikon=()
    )
    realia_repository._realia_collection.insert_one(RealiaEntrySchema().dump(entry))


def stored_reallexikon_entry(identifier: str, bibliography_id: str, pages: str) -> dict:
    return {
        "id": identifier,
        "title": f"Aššur {identifier}",
        "reference": {"id": bibliography_id, "pages": pages},
    }
