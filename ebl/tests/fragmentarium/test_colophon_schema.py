from ebl.fragmentarium.application.colophon_schema import (
    ColophonSchema,
    NameAttestationSchema,
    ProvenanceAttestationSchema,
    ColophonStatus,
    ColophonType,
    ColophonOwnership,
    IndividualType,
    IndividualTypeAttestationSchema,
)
from ebl.fragmentarium.domain.colophon import (
    NameAttestation,
    ProvenanceAttestation,
)
from ebl.common.domain.provenance import Provenance

name_attestation = {"value": "John Doe"}
type_attestation = {"value": IndividualType.Scribe}
provenance_attestation = {"value": Provenance.BABYLON.long_name}
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
            "type": type_attestation,
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
    assert deserialized.value == Provenance.BABYLON.long_name


def test_colophon_schema_integration():
    schema = ColophonSchema()
    serialized = schema.dump(colophon_data)
    deserialized = schema.load(serialized)
    provenance_deserialized = ProvenanceAttestationSchema().load(provenance_attestation)
    name_deserialized = NameAttestationSchema().load(name_attestation)
    type_deserialized = IndividualTypeAttestationSchema().load(type_attestation)
    assert deserialized.colophon_status == ColophonStatus.OnlyColophon
    assert deserialized.colophon_ownership == ColophonOwnership.Individual
    assert deserialized.colophon_types == [ColophonType.AsbD]
    assert deserialized.original_from == provenance_deserialized
    assert deserialized.written_in == provenance_deserialized
    assert deserialized.notes_to_scribal_process == "Some notes"
    assert deserialized.individuals[0].name == name_deserialized
    assert deserialized.individuals[0].son_of == name_deserialized
    assert deserialized.individuals[0].grandson_of is None
    assert deserialized.individuals[0].type == type_deserialized
    assert isinstance(deserialized.original_from, ProvenanceAttestation)
