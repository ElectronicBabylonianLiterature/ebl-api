from marshmallow import Schema, fields, post_load

from ebl.fragmentarium.domain.named_entity import NamedEntity, NamedEntityType


class NamedEntitySchema(Schema):
    id = fields.String(required=True)
    type = fields.Function(
        lambda entity: entity.type.long_name,
        lambda value: NamedEntityType.from_name(value),
        required=True,
    )

    @post_load
    def make_entity(self, data, **kwargs) -> NamedEntity:
        return NamedEntity(**data)
