from typing import cast

import pytest

from ebl.bibliography.domain.reference import ReferenceType
from ebl.realia.domain.realia_entry import (
    AfoRegisterEntry,
    RealiaEntry,
    ReallexikonEntry,
)
from ebl.realia.infrastructure.realia_schemas import (
    AfoRegisterEntrySchema,
    RealiaEntrySchema,
    ReallexikonEntrySchema,
)
from ebl.tests.factories.realia import RealiaEntryFactory


def _load_reallexikon(data: dict) -> ReallexikonEntry:
    return cast(ReallexikonEntry, ReallexikonEntrySchema().load(data))


def _load_realia(data: dict) -> RealiaEntry:
    return cast(RealiaEntry, RealiaEntrySchema().load(data))


@pytest.fixture
def realia_entry() -> RealiaEntry:
    return RealiaEntryFactory.build()


def test_realia_entry_defaults() -> None:
    entry = RealiaEntry(id="Lion")
    assert entry.id == "Lion"
    assert entry.realia_id == ""
    assert entry.related_terms == ()
    assert entry.type == ()
    assert entry.afo_register == ()
    assert entry.references == ()
    assert entry.wikidata_id == ()
    assert entry.reallexikon == ()
    assert entry.cross_references == ()
    assert entry.afo_cross_references == ()


def test_afo_register_entry_defaults() -> None:
    entry = AfoRegisterEntry()
    assert entry.afo_volume == ""
    assert entry.page == ""
    assert entry.cross_references == ()


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
    dumped = cast(dict, AfoRegisterEntrySchema().dump(entry))
    assert dumped == {
        "mainWord": "silver",
        "note": "precious metal",
        "AfO": "AfO 50",
        "reference": "p. 42",
        "crossReference": "see gold",
        "afoVolume": "",
        "page": "",
        "crossReferences": [],
    }
    loaded = AfoRegisterEntrySchema().load(dumped)
    assert loaded == entry


def test_reallexikon_entry_schema_round_trip() -> None:
    entry = ReallexikonEntry(id="Lion", title="Lion, Löwe", reference=None)
    dumped = cast(dict, ReallexikonEntrySchema().dump(entry))
    assert dumped["id"] == "Lion"
    assert dumped["title"] == "Lion, Löwe"
    assert dumped["reference"] is None
    assert "content" not in dumped
    loaded = _load_reallexikon(dumped)
    assert loaded == entry


@pytest.mark.parametrize(
    "reference_id",
    [
        pytest.param(5, id="integer"),
        pytest.param({"nested": "bib_1"}, id="object"),
        pytest.param(["bib_1"], id="list"),
    ],
)
def test_reallexikon_non_string_reference_id_deserializes_to_none(
    reference_id: object,
) -> None:
    entry = _load_reallexikon({"id": "Lion", "reference": {"id": reference_id}})

    assert entry.reference is None


def test_reallexikon_lean_reference_deserializes_with_pages() -> None:
    entry = _load_reallexikon(
        {
            "id": "1069",
            "title": "Aššur A.",
            "reference": {"id": "rla_1_170e", "pages": "170–195"},
        }
    )
    reference = entry.reference
    assert reference is not None
    assert reference.id == "rla_1_170e"
    assert reference.type == ReferenceType.DISCUSSION
    assert reference.pages == "170–195"


def test_reallexikon_empty_reference_id_deserializes_to_none() -> None:
    assert _load_reallexikon({"id": "x", "reference": ""}).reference is None
    assert _load_reallexikon({"id": "x", "reference": {"pages": "1"}}).reference is None
    assert _load_reallexikon({"id": "x", "reference": []}).reference is None


def test_realia_entry_schema_dump(realia_entry: RealiaEntry) -> None:
    dumped = cast(dict, RealiaEntrySchema().dump(realia_entry))
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
    entry = _load_realia(data)
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
            {
                "id": "4",
                "title": "Aakalla",
                "reference": {"id": "rla_1_2b", "pages": "2"},
            }
        ],
    }
    entry = _load_realia(data)
    assert entry.type == ("Personal names",)
    reference = entry.reallexikon[0].reference
    assert reference is not None
    assert reference.id == "rla_1_2b"
    assert reference.pages == "2"


def test_realia_entry_schema_load_multiple_reallexikon() -> None:
    data = {
        "_id": "Aššur",
        "relatedTerms": [],
        "type": [],
        "afoRegister": [],
        "references": [],
        "wikidataId": [],
        "reallexikon": [
            {
                "id": "1069",
                "title": "Aššur A. Stadt",
                "reference": {"id": "rla_1_170e", "pages": "170–195"},
            },
            {
                "id": "1070",
                "title": "Aššur B. Land",
                "reference": {"id": "rla_1_195", "pages": "195–198"},
            },
            {"id": "1071", "title": "Aššur C. Gott", "reference": None},
        ],
    }
    entry = _load_realia(data)
    assert tuple(rlex.id for rlex in entry.reallexikon) == ("1069", "1070", "1071")
    first_reference = entry.reallexikon[0].reference
    assert first_reference is not None
    assert first_reference.id == "rla_1_170e"
    assert entry.reallexikon[2].reference is None
