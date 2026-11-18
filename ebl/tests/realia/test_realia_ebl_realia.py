from typing import cast

import falcon
import pytest
from falcon import testing
from marshmallow import ValidationError

from ebl.bibliography.application.bibliography_repository import BibliographyRepository
from ebl.bibliography.domain.reference import BibliographyId, Reference, ReferenceType
from ebl.realia.domain.realia_entry import EblRealiaEntry, RealiaEntry
from ebl.realia.infrastructure.mongo_realia_repository import MongoRealiaRepository
from ebl.realia.infrastructure.realia_schemas import (
    EblRealiaEntrySchema,
    RealiaEntrySchema,
)
from ebl.tests.factories.bibliography import (
    BibliographyEntryFactory,
    ReferenceFactory,
)
from ebl.tests.factories.realia import EblRealiaEntryFactory, RealiaEntryFactory
from ebl.tests.realia.realia_repository_helpers import (
    create_entry_with_bibliography,
    insert_stored,
)

STAR_REFERENCE = {"id": "jones2004study", "pages": "482"}

STAR_ENTRY = {
    "id": "MÚL KUR šá DUR nu-nu",
    "transliteration": "MÚL KUR šá DUR nu-nu",
    "normalisation": "",
    "translation": "The bright star of the ribbon of the fishes",
    "identification": "η Psc",
    "pos": "CN",
    "wikidataId": ["Q14068"],
    "reference": STAR_REFERENCE,
    "remarks": "",
}

STAR_DOCUMENT = {
    "_id": "η Piscium",
    "realiaId": "realia_028434",
    "lemma": "η Piscium",
    "relatedTerms": ["η Psc", "Eta Piscium", "MÚL KUR šá DUR nu-nu"],
    "type": ["Astronomy"],
    "referenceType": ["eBL"],
    "wikidataId": ["Q14068"],
    "crossReferences": [],
    "afoCrossReferences": [],
    "reallexikon": [],
    "afoRegister": [],
    "eblRealia": [STAR_ENTRY],
    "references": [
        {**STAR_REFERENCE, "type": "DISCUSSION", "notes": "", "linesCited": []}
    ],
}

STAR_REFERENCE_MODEL = Reference(
    BibliographyId("jones2004study"), ReferenceType.DISCUSSION, pages="482"
)


def _load(document: dict) -> RealiaEntry:
    return cast(RealiaEntry, RealiaEntrySchema().load(document))


def test_ebl_realia_entry_defaults() -> None:
    assert cast(EblRealiaEntry, EblRealiaEntrySchema().load({})) == EblRealiaEntry()


def test_star_document_loads_reference_type_and_ebl_realia() -> None:
    entry = _load(STAR_DOCUMENT)

    assert entry.reference_type == ("eBL",)
    assert entry.ebl_realia == (
        EblRealiaEntry(
            id="MÚL KUR šá DUR nu-nu",
            transliteration="MÚL KUR šá DUR nu-nu",
            translation="The bright star of the ribbon of the fishes",
            identification="η Psc",
            pos="CN",
            wikidata_id=("Q14068",),
            reference=STAR_REFERENCE_MODEL,
        ),
    )


def test_document_without_new_fields_loads_and_dumps_empty_lists() -> None:
    entry = _load({"_id": "Anu"})

    assert entry.reference_type == ()
    assert entry.ebl_realia == ()
    dumped = cast(dict, RealiaEntrySchema().dump(entry))
    assert dumped["referenceType"] == []
    assert dumped["eblRealia"] == []


@pytest.mark.parametrize("field", ["title", "afoVolume"])
def test_ebl_realia_entry_rejects_fields_of_other_entry_types(field: str) -> None:
    with pytest.raises(ValidationError):
        EblRealiaEntrySchema().load({**STAR_ENTRY, field: "x"})


def test_ebl_realia_entry_round_trip() -> None:
    entry = EblRealiaEntryFactory.build(reference=None)

    dumped = cast(dict, EblRealiaEntrySchema().dump(entry))

    assert dumped["wikidataId"] == list(entry.wikidata_id)
    assert dumped["reference"] is None
    assert EblRealiaEntrySchema().load(dumped) == entry


def test_repository_injects_ebl_realia_bibliography(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
) -> None:
    reference = ReferenceFactory.build(
        type=ReferenceType.DISCUSSION, notes="", lines_cited=(), with_document=True
    )
    entry = RealiaEntryFactory.build(
        ebl_realia=(
            EblRealiaEntryFactory.build(reference=reference),
            EblRealiaEntryFactory.build(reference=None),
        )
    )
    create_entry_with_bibliography(realia_repository, bibliography_repository, entry)

    assert realia_repository.find(entry.id).ebl_realia == entry.ebl_realia


def test_get_star_by_realia_id(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
    client: testing.TestClient,
) -> None:
    bibliography = BibliographyEntryFactory.build(id="jones2004study")
    bibliography_repository.create(bibliography)
    insert_stored(realia_repository, STAR_DOCUMENT)

    result = cast(testing.Result, client.simulate_get("/realia/by-id/realia_028434"))

    assert result.status == falcon.HTTP_OK
    payload = cast(dict, result.json)
    assert payload["referenceType"] == ["eBL"]
    [ebl_entry] = payload["eblRealia"]
    assert {key: ebl_entry[key] for key in STAR_ENTRY if key != "reference"} == {
        key: value for key, value in STAR_ENTRY.items() if key != "reference"
    }
    assert ebl_entry["reference"]["id"] == "jones2004study"
    assert ebl_entry["reference"]["pages"] == "482"
    assert ebl_entry["reference"]["type"] == "DISCUSSION"
    assert ebl_entry["reference"]["document"]["id"] == "jones2004study"


def test_get_entry_without_new_fields(
    realia_repository: MongoRealiaRepository, client: testing.TestClient
) -> None:
    insert_stored(realia_repository, {"_id": "Anu", "realiaId": "realia_000001"})

    result = cast(testing.Result, client.simulate_get("/realia/by-id/realia_000001"))

    assert result.status == falcon.HTTP_OK
    payload = cast(dict, result.json)
    assert payload["referenceType"] == []
    assert payload["eblRealia"] == []
