from typing import Optional

from marshmallow import Schema, ValidationError, fields, post_load, validate

from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.common.domain.accession import Accession
from ebl.provenance.domain.provenance_model import ProvenanceRecord


class AbstractMuseumNumberSchema(Schema):
    prefix = fields.String(required=True, validate=validate.Length(min=1))
    number = fields.String(
        required=True, validate=(validate.Length(min=1), validate.ContainsNoneOf("."))
    )
    suffix = fields.String(required=True, validate=validate.ContainsNoneOf("."))


class AccessionSchema(AbstractMuseumNumberSchema):
    @post_load
    def create_accession(self, data, **kwargs) -> Accession:
        return Accession(**data)


def deserialize_provenance_record(
    schema: Schema, value: Optional[str]
) -> Optional[ProvenanceRecord]:
    if not value:
        return None
    provenance_service = schema.context.get("provenance_service")
    if not isinstance(provenance_service, ProvenanceService):
        raise ValidationError("Provenance service not configured.")
    record = provenance_service.find_by_name(value)
    if record is None:
        raise ValidationError(f"Invalid provenance: {value}")
    return record
