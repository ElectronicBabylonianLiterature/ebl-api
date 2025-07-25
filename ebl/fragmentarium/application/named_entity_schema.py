from marshmallow import Schema, fields, post_load

from ebl.fragmentarium.domain.named_entity import (
    EntityAnnotationSpan,
    NamedEntity,
    NamedEntityType,
)


class AbstractNamedEntitySchema(Schema):
    id = fields.String(required=True)
    type = fields.Function(
        lambda entity: entity.type.long_name,
        lambda value: NamedEntityType.from_name(value),
        required=True,
    )


class NamedEntitySchema(AbstractNamedEntitySchema):
    @post_load
    def make_entity(self, data, **kwargs) -> NamedEntity:
        return NamedEntity(**data)


class EntityAnnotationSpanSchema(AbstractNamedEntitySchema):
    span = fields.List(fields.String(), required=True)

    @post_load
    def make_entity_span(self, data, **kwargs) -> EntityAnnotationSpan:
        return EntityAnnotationSpan(**data)
