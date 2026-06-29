import pytest
from marshmallow import ValidationError

from ebl.realia.domain.realia_entry import (
    AfoCrossReference,
    CrossReference,
    RealiaEntry,
)
from ebl.realia.infrastructure.realia_schemas import (
    AfoCrossReferenceSchema,
    CrossReferenceSchema,
    RealiaEntrySchema,
)


def test_cross_reference_schema_round_trip() -> None:
    cross_reference = CrossReference(id="realia_003277", lemma="Elam (Geschichte)")
    dumped = CrossReferenceSchema().dump(cross_reference)
    assert dumped == {"id": "realia_003277", "lemma": "Elam (Geschichte)"}
    assert CrossReferenceSchema().load(dumped) == cross_reference


def test_cross_reference_requires_id_and_lemma() -> None:
    with pytest.raises(ValidationError):
        CrossReferenceSchema().load({"id": "realia_003277"})
    with pytest.raises(ValidationError):
        CrossReferenceSchema().load({"lemma": "Elam"})


def test_afo_cross_reference_schema_round_trip() -> None:
    cross_reference = AfoCrossReference(
        id="realia_003277", lemma="Elam (Geschichte)", afo_volume="AfO 52", page="645"
    )
    dumped = AfoCrossReferenceSchema().dump(cross_reference)
    assert dumped == {
        "id": "realia_003277",
        "lemma": "Elam (Geschichte)",
        "afoVolume": "AfO 52",
        "page": "645",
    }
    assert AfoCrossReferenceSchema().load(dumped) == cross_reference


def test_afo_cross_reference_requires_volume_and_page() -> None:
    base = {"id": "realia_003277", "lemma": "Elam"}
    with pytest.raises(ValidationError):
        AfoCrossReferenceSchema().load(base)
    with pytest.raises(ValidationError):
        AfoCrossReferenceSchema().load({**base, "afoVolume": "AfO 52"})
    with pytest.raises(ValidationError):
        AfoCrossReferenceSchema().load({**base, "page": "645"})


def test_realia_entry_schema_load_cross_references() -> None:
    data = {
        "_id": "Elam (Geschichte)",
        "realiaId": "realia_003277",
        "crossReferences": [{"id": "realia_000001", "lemma": "Anšan"}],
        "afoCrossReferences": [
            {
                "id": "realia_000002",
                "lemma": "Susa",
                "afoVolume": "AfO 52",
                "page": "645",
            }
        ],
        "afoRegister": [
            {
                "mainWord": "Elam",
                "afoVolume": "AfO 52",
                "page": "645",
                "crossReferences": [
                    {
                        "id": "realia_000003",
                        "lemma": "Anšan",
                        "afoVolume": "AfO 52",
                        "page": "646",
                    }
                ],
            }
        ],
    }
    entry = RealiaEntrySchema().load(data)
    assert entry.realia_id == "realia_003277"
    assert entry.cross_references == (
        CrossReference(id="realia_000001", lemma="Anšan"),
    )
    assert entry.afo_cross_references == (
        AfoCrossReference(
            id="realia_000002", lemma="Susa", afo_volume="AfO 52", page="645"
        ),
    )
    assert entry.afo_register[0].afo_volume == "AfO 52"
    assert entry.afo_register[0].page == "645"
    assert entry.afo_register[0].cross_references == (
        AfoCrossReference(
            id="realia_000003", lemma="Anšan", afo_volume="AfO 52", page="646"
        ),
    )


def test_realia_entry_cross_reference_lists_default_to_empty() -> None:
    entry = RealiaEntrySchema().load({"_id": "Elam"})
    assert entry.realia_id == ""
    assert entry.cross_references == ()
    assert entry.afo_cross_references == ()
    assert entry.afo_register == ()


def test_realia_entry_schema_dump_cross_references() -> None:
    entry = RealiaEntry(
        id="Elam (Geschichte)",
        realia_id="realia_003277",
        cross_references=(CrossReference(id="realia_000001", lemma="Anšan"),),
        afo_cross_references=(
            AfoCrossReference(
                id="realia_000002", lemma="Susa", afo_volume="AfO 52", page="645"
            ),
        ),
    )
    dumped = RealiaEntrySchema().dump(entry)
    assert dumped["realiaId"] == "realia_003277"
    assert dumped["crossReferences"] == [{"id": "realia_000001", "lemma": "Anšan"}]
    assert dumped["afoCrossReferences"] == [
        {
            "id": "realia_000002",
            "lemma": "Susa",
            "afoVolume": "AfO 52",
            "page": "645",
        }
    ]
