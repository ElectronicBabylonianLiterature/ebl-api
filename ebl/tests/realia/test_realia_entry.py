import pytest

from ebl.realia.domain.realia_entry import (
    AfoRegisterEntry,
    RealiaEntry,
    ReallexikonEntry,
)
from ebl.realia.infrastructure.mongo_realia_repository import (
    AfoRegisterEntrySchema,
    RealiaEntrySchema,
    ReallexikonEntrySchema,
)
from ebl.tests.factories.realia import RealiaEntryFactory


@pytest.fixture
def realia_entry() -> RealiaEntry:
    return RealiaEntryFactory.build()


def test_realia_entry_defaults() -> None:
    entry = RealiaEntry(id="Lion")
    assert entry.id == "Lion"
    assert entry.related_terms == ()
    assert entry.type == ()
    assert entry.afo_register == ()
    assert entry.references == ()
    assert entry.wikidata_id == ()
    assert entry.reallexikon == ()


def test_realia_entry_creation(realia_entry: RealiaEntry) -> None:
    assert realia_entry.id is not None
    assert isinstance(realia_entry.related_terms, tuple)
    assert isinstance(realia_entry.type, tuple)
    assert all(isinstance(t, str) for t in realia_entry.type)
    assert isinstance(realia_entry.afo_register, tuple)
    assert all(isinstance(e, AfoRegisterEntry) for e in realia_entry.afo_register)
    assert isinstance(realia_entry.references, tuple)
    assert isinstance(realia_entry.wikidata_id, tuple)
    assert isinstance(realia_entry.reallexikon, tuple)
    assert all(isinstance(r, ReallexikonEntry) for r in realia_entry.reallexikon)


def test_afo_register_entry_schema_round_trip() -> None:
    entry = AfoRegisterEntry(
        main_word="silver",
        note="precious metal",
        afo="AfO 50",
        reference="p. 42",
        cross_reference="see gold",
    )
    dumped = AfoRegisterEntrySchema().dump(entry)
    assert dumped == {
        "mainWord": "silver",
        "note": "precious metal",
        "AfO": "AfO 50",
        "reference": "p. 42",
        "crossReference": "see gold",
    }
    loaded = AfoRegisterEntrySchema().load(dumped)
    assert loaded == entry


def test_reallexikon_entry_schema_round_trip() -> None:
    entry = ReallexikonEntry(id="Lion", title="Lion, Löwe", reference=None, content="")
    dumped = ReallexikonEntrySchema().dump(entry)
    assert dumped["id"] == "Lion"
    assert dumped["title"] == "Lion, Löwe"
    assert dumped["reference"] is None
    assert dumped["content"] == ""
    loaded = ReallexikonEntrySchema().load(dumped)
    assert loaded == entry


def test_realia_entry_schema_dump(realia_entry: RealiaEntry) -> None:
    dumped = RealiaEntrySchema().dump(realia_entry)
    assert dumped["_id"] == realia_entry.id
    assert dumped["relatedTerms"] == list(realia_entry.related_terms)
    assert dumped["type"] == list(realia_entry.type)
    assert dumped["wikidataId"] == list(realia_entry.wikidata_id)
    assert len(dumped["afoRegister"]) == len(realia_entry.afo_register)
    assert len(dumped["reallexikon"]) == len(realia_entry.reallexikon)


def test_realia_entry_schema_load_round_trip() -> None:
    data = {
        "_id": "Bronze",
        "relatedTerms": ["Kupfer", "Metall"],
        "type": ["Personal names"],
        "afoRegister": [],
        "references": [],
        "wikidataId": ["Q34095"],
        "reallexikon": [],
    }
    entry = RealiaEntrySchema().load(data)
    assert entry.id == "Bronze"
    assert entry.related_terms == ("Kupfer", "Metall")
    assert entry.type == ("Personal names",)
    assert entry.wikidata_id == ("Q34095",)


def test_realia_entry_schema_load_stored_shape() -> None:
    data = {
        "_id": "Aakalla",
        "relatedTerms": ["A-a-kal-la"],
        "type": ["Personal names"],
        "afoRegister": [],
        "references": [],
        "wikidataId": [],
        "reallexikon": [
            {"id": "4", "title": "Aakalla", "reference": "rla_1_2b", "content": ""}
        ],
    }
    entry = RealiaEntrySchema().load(data)
    assert entry.type == ("Personal names",)
    reference = entry.reallexikon[0].reference
    assert reference is not None
    assert reference.id == "rla_1_2b"


def test_realia_entry_schema_load_multiple_reallexikon() -> None:
    data = {
        "_id": "Aššur",
        "relatedTerms": [],
        "type": [],
        "afoRegister": [],
        "references": [],
        "wikidataId": [],
        "reallexikon": [
            {"id": "1069", "title": "Aššur A. Stadt", "reference": "", "content": ""},
            {"id": "1070", "title": "Aššur B. Land", "reference": "", "content": ""},
            {"id": "1071", "title": "Aššur C. Gott", "reference": "", "content": ""},
        ],
    }
    entry = RealiaEntrySchema().load(data)
    assert tuple(rlex.id for rlex in entry.reallexikon) == ("1069", "1070", "1071")
