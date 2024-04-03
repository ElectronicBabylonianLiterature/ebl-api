from marshmallow import Schema, fields, post_load
from ebl.schemas import ValueEnumField
from ebl.fragmentarium.domain.colophon import (
    ColophonStatus,
    ColophonType,
    NameAttestation,
    ProvenanceAttestation,
    IndividualAttestation,
    Colophon,
)
from ebl.common.domain.provenance import Provenance


class NameAttestationSchema(Schema):
    value = fields.String(allow_none=True)
    isBroken = fields.Boolean(data_key="is_broken", allow_none=True)
    isUncertain = fields.Boolean(data_key="is_uncertain", allow_none=True)

    @post_load
    def make_name_attestation(self, data, **kwargs):
        return NameAttestation(**data)


class ProvenanceAttestationSchema(Schema):
    value = ValueEnumField(Provenance, allow_none=True)
    isBroken = fields.Boolean(data_key="is_broken", allow_none=True)
    isUncertain = fields.Boolean(data_key="is_uncertain", allow_none=True)

    @post_load
    def make_provenance_attestation(self, data, **kwargs):
        return ProvenanceAttestation(**data)


class ColophonStatusSchema(Schema):
    value = ValueEnumField(ColophonStatus, allow_none=True)
    isBroken = fields.Boolean(data_key="is_broken", allow_none=True)
    isUncertain = fields.Boolean(data_key="is_uncertain", allow_none=True)


class IndividualAttestationSchema(Schema):
    name = fields.Nested(NameAttestationSchema, allow_none=True)
    sonOf = fields.Nested(NameAttestationSchema, allow_none=True, data_key="son_of")
    grandsonOf = fields.Nested(
        NameAttestationSchema, allow_none=True, data_key="grandson_of"
    )
    family = fields.Nested(NameAttestationSchema, allow_none=True)
    nativeOf = fields.Nested(
        ProvenanceAttestationSchema, allow_none=True, data_key="native_of"
    )
    type = ValueEnumField(ColophonStatus, allow_none=True)

    @post_load
    def make_individual_attestation(self, data, **kwargs):
        return IndividualAttestation(**data)


class ColophonSchema(Schema):
    colophonStatus = ValueEnumField(
        ColophonStatus, allow_none=True, data_key="colophon_status"
    )
    colophonOwnership = ValueEnumField(
        ColophonStatus, allow_none=True, data_key="colophon_ownership"
    )
    colophonTypes = fields.List(
        ValueEnumField(ColophonType), allow_none=True, data_key="colophon_types"
    )
    originalFrom = fields.Nested(
        ProvenanceAttestationSchema, allow_none=True, data_key="original_from"
    )
    writtenIn = fields.Nested(
        ProvenanceAttestationSchema, allow_none=True, data_key="written_in"
    )
    notesToScribalProcess = fields.String(
        allow_none=True, data_key="notes_to_scribal_process"
    )
    individuals = fields.List(
        fields.Nested(IndividualAttestationSchema), allow_none=True
    )

    @post_load
    def make_colophon(self, data, **kwargs):
        return Colophon(**data)
