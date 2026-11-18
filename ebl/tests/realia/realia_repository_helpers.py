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
    section_references = [
        reallexikon_entry.reference for reallexikon_entry in entry.reallexikon
    ] + [ebl_realia_entry.reference for ebl_realia_entry in entry.ebl_realia]
    for reference in [*entry.references, *section_references]:
        if reference is not None and reference.document:
            bibliography_repository.create(reference.document)


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
