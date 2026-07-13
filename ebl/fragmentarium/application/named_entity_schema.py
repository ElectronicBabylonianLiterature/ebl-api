from typing import Mapping, Type, Union, cast

from marshmallow import Schema, ValidationError, fields, post_load, validate
from marshmallow_oneofschema.one_of_schema import OneOfSchema

from ebl.fragmentarium.domain.named_entity import (
    REALIA_ID_PATTERN,
    AnnotationEntity,
    AnnotationSpan,
    EntityAnnotationSpan,
    NamedEntity,
    NamedEntityType,
    RealiaAnnotationSpan,
    RealiaEntity,
)

ENTITY_TYPE = "entity"
REALIA_TYPE = "realia"
REALIA_ID_KEY = "realiaId"
TYPE_KEY = "type"


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
    def make_entity_span(self, data, **kwargs) -> RealiaAnnotationSpan:
        return RealiaAnnotationSpan(**data)


class AbstractAnnotationSchema(OneOfSchema):
    def get_obj_type(self, obj: Union[AnnotationEntity, AnnotationSpan]) -> str:
        return REALIA_TYPE if isinstance(obj, RealiaEntity) else ENTITY_TYPE

    def get_data_type(self, data: dict) -> str:
        has_realia_id = REALIA_ID_KEY in data
        has_type = TYPE_KEY in data
        if has_realia_id == has_type:
            raise ValidationError(
                {
                    "_schema": [
                        f"Exactly one of '{TYPE_KEY}' and '{REALIA_ID_KEY}' is required."
                    ]
                }
            )
        return REALIA_TYPE if has_realia_id else ENTITY_TYPE

    def _dump(self, obj, *, update_fields: bool = True, **kwargs) -> dict:
        type_schema = self.type_schemas[self.get_obj_type(obj)]
        schema = type_schema if isinstance(type_schema, Schema) else type_schema()
        return cast(dict, schema.dump(obj, many=False))


class AnnotationEntitySchema(AbstractAnnotationSchema):
    type_schemas: Mapping[str, Union[Type[Schema], Schema]] = {
        ENTITY_TYPE: NamedEntitySchema,
        REALIA_TYPE: RealiaEntitySchema,
    }


class AnnotationSpanSchema(AbstractAnnotationSchema):
    type_schemas: Mapping[str, Union[Type[Schema], Schema]] = {
        ENTITY_TYPE: EntityAnnotationSpanSchema,
        REALIA_TYPE: RealiaAnnotationSpanSchema,
    }
