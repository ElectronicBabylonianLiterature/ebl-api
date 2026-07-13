from marshmallow import Schema, fields, post_load, validate

from ebl.fragmentarium.domain.named_entity import (
    REALIA_ID_PATTERN,
    EntityAnnotationSpan,
    NamedEntity,
    NamedEntityType,
    RealiaAnnotationSpan,
    RealiaEntity,
)

REALIA_ID_KEY = "realiaId"


class AbstractNamedEntitySchema(Schema):
    id = fields.String(required=True)
    type = fields.Function(
        lambda entity: entity.type.long_name,
        lambda value: NamedEntityType.from_name(value),
        required=True,
    )


class AbstractRealiaEntitySchema(Schema):
    id = fields.String(required=True)
    realia_id = fields.String(
        required=True,
        data_key=REALIA_ID_KEY,
        validate=validate.Regexp(REALIA_ID_PATTERN),
    )


class NamedEntitySchema(AbstractNamedEntitySchema):
    @post_load
    def make_entity(self, data, **kwargs) -> NamedEntity:
        return NamedEntity(**data)


class RealiaEntitySchema(AbstractRealiaEntitySchema):
    @post_load
    def make_entity(self, data, **kwargs) -> RealiaEntity:
        return RealiaEntity(**data)


class EntityAnnotationSpanSchema(AbstractNamedEntitySchema):
    span = fields.List(fields.String(), required=True)

    @post_load
    def make_entity_span(self, data, **kwargs) -> EntityAnnotationSpan:
        return EntityAnnotationSpan(**data)


class RealiaAnnotationSpanSchema(AbstractRealiaEntitySchema):
    span = fields.List(fields.String(), required=True)

    @post_load
    def make_realia_span(self, data, **kwargs) -> RealiaAnnotationSpan:
        return RealiaAnnotationSpan(**data)
