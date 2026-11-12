from typing import Optional

from marshmallow import ValidationError, fields, validate

from ebl.sumerian_dictionary.domain.sumerian_word_links import (
    Alias,
    CrossReference,
    WordLink,
)
from ebl.sumerian_dictionary.infrastructure.sumerian_schema_base import (
    ALIAS_RELATIONS,
    ATTINGER_SOURCE,
    CROSS_REFERENCE_RELATIONS,
    AttrsSchema,
)


class WordLinkSchema(AttrsSchema):
    model = WordLink

    id = fields.String(required=True)
    citation_form = fields.String(required=True, data_key="citationForm")
    homonym = fields.String(load_default="")
    guide_word = fields.String(data_key="guideWord", load_default="")


class HeadIdField(fields.Field):
    def _serialize(
        self, value: Optional[WordLink], attr, obj, **kwargs
    ) -> Optional[str]:
        return None if value is None else value.id

    def _deserialize(self, value: object, attr, data, **kwargs) -> WordLink:
        if not isinstance(value, str):
            raise ValidationError("Not a valid word id.")
        return WordLink(value, "")


class CrossReferenceSchema(AttrsSchema):
    model = CrossReference

    relation = fields.String(
        required=True, validate=validate.OneOf(CROSS_REFERENCE_RELATIONS)
    )
    target = fields.String(required=True)
    method = fields.String(required=True)
    targets = fields.List(fields.Nested(WordLinkSchema), load_default=list)
    name_targets = fields.List(
        fields.Nested(WordLinkSchema), data_key="nameTargets", load_default=list
    )
    ambiguous = fields.Boolean(load_default=False)


class AliasSchema(AttrsSchema):
    model = Alias

    form = fields.String(required=True)
    relation = fields.String(required=True, validate=validate.OneOf(ALIAS_RELATIONS))
    entry_id = fields.String(required=True, data_key="entryId")
    method = fields.String(required=True)
    source = fields.String(required=True, validate=validate.OneOf(ATTINGER_SOURCE))
    meanings = fields.List(fields.String(), load_default=list)
    uncertain = fields.Boolean(load_default=False)
