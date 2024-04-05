from ebl.fragmentarium.application.colophon_schema import (
    ColophonSchema,
    NameAttestationSchema,
    ProvenanceAttestationSchema,
    ColophonStatus,
    ColophonType,
    ColophonOwnership,
    IndividualType,
    Provenance,
)
from ebl.fragmentarium.domain.colophon import (
    NameAttestation,
    ProvenanceAttestation,
)

name_attestation = {"value": "John Doe"}
provenance_attestation = {"value": "Provenance.BABYLON"}
colophon_data = {
    "colophon_status": ColophonStatus.OnlyColophon,
    "colophon_ownership": ColophonOwnership.Individual,
    "colophon_types": [ColophonType.AsbD],
    "original_from": provenance_attestation,
    "written_in": provenance_attestation,
    "notes_to_scribal_process": "Some notes",
    "individuals": [
        {
            "name": name_attestation,
            "son_of": name_attestation,
            "type": IndividualType.Scribe,
        }
    ],
}


def test_name_attestation_schema():
    attestation = name_attestation
    schema = NameAttestationSchema()
    serialized = schema.dump(attestation)
    deserialized = schema.load(serialized)
    assert isinstance(deserialized, NameAttestation)
    assert deserialized.value == attestation["value"]


def test_provenance_attestation_schema():
    attestation = provenance_attestation
    schema = ProvenanceAttestationSchema()
    serialized = schema.dump(attestation)
    deserialized = schema.load(serialized)
    assert isinstance(deserialized, ProvenanceAttestation)
    assert deserialized.value == Provenance.BABYLON


def test_colophon_schema_integration():
    schema = ColophonSchema()
    serialized = schema.dump(colophon_data)
    deserialized = schema.load(serialized)
    provenance_deserialized = ProvenanceAttestationSchema().load(provenance_attestation)
    name_deserialized = NameAttestationSchema().load(name_attestation)
    assert deserialized.colophon_status == ColophonStatus.OnlyColophon
    assert deserialized.colophon_ownership == ColophonOwnership.Individual
    assert deserialized.colophon_types == [ColophonType.AsbD]
    assert deserialized.original_from == provenance_deserialized
    assert deserialized.written_in == provenance_deserialized
    assert deserialized.notes_to_scribal_process == "Some notes"
    assert deserialized.individuals[0].name == name_deserialized
    assert deserialized.individuals[0].son_of == name_deserialized
    assert deserialized.individuals[0].grandson_of is None
    assert deserialized.individuals[0].type == IndividualType.Scribe
    assert isinstance(deserialized.original_from, ProvenanceAttestation)
