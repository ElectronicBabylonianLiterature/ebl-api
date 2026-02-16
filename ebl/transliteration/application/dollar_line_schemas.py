from typing import Mapping, Type, Union

from marshmallow import Schema, fields, post_load

from ebl.schemas import NameEnumField
from ebl.transliteration.application.line_schemas import LineBaseSchema
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.dollar_line import (
    ImageDollarLine,
    LooseDollarLine,
    RulingDollarLine,
    ScopeContainer,
    StateDollarLine,
    SealDollarLine,
)
from ebl.transliteration.domain.tokens import ValueToken


class DollarLineSchema(LineBaseSchema):
    prefix = fields.Constant("$")
    content = fields.Function(
        lambda obj: [OneOfTokenSchema().dump(ValueToken.of(f" {obj.display_value}"))],
        lambda value: value,
    )


class LooseDollarLineSchema(DollarLineSchema):
    text = fields.String(required=True)
    display_value = fields.String(data_key="displayValue")

    @post_load
    def make_line(self, data, **kwargs) -> LooseDollarLine:
        return LooseDollarLine(data["text"])


class ImageDollarLineSchema(DollarLineSchema):
    number = fields.String(required=True)
    letter = fields.String(required=True, allow_none=True)
    text = fields.String(required=True)
    display_value = fields.String(data_key="displayValue")

    @post_load
    def make_line(self, data, **kwargs) -> ImageDollarLine:
        return ImageDollarLine(data["number"], data["letter"], data["text"])


class RulingDollarLineSchema(DollarLineSchema):
    number = NameEnumField(atf.Ruling, required=True)
    status = NameEnumField(atf.DollarStatus, load_default=None)
    display_value = fields.String(data_key="displayValue")

    @post_load
    def make_line(self, data, **kwargs) -> RulingDollarLine:
        return RulingDollarLine(data["number"], data["status"])


class SealDollarLineSchema(DollarLineSchema):
    number = fields.Int(required=True)
    display_value = fields.String(data_key="displayValue")

    @post_load
    def make_line(self, data, **kwargs) -> SealDollarLine:
        return SealDollarLine(data["number"])


class ScopeContainerSchema(Schema):
    type = fields.Function(
        # pyre-ignore[29]
        lambda scope_container: type(scope_container.content).__name__,
        lambda value: value,
        required=True,
    )
    content = fields.Function(
        lambda scope_container: scope_container.content.name,
        lambda value: value,
        required=True,
    )
    text = fields.String(required=True)
    display_value = fields.String(data_key="displayValue")

    @post_load
    def make__scope_container(self, data, **kwargs) -> ScopeContainer:
        return ScopeContainer(
            self.load_scope(data["type"], data["content"]), data["text"]
        )

    def load_scope(
        self, type: str, content: str
    ) -> Union[atf.Surface, atf.Scope, atf.Object]:
        scope_types: Mapping[str, Type[Union[atf.Surface, atf.Scope, atf.Object]]] = {
            "Surface": atf.Surface,
            "Scope": atf.Scope,
            "Object": atf.Object,
        }
        return scope_types[type][content]


class StateDollarLineSchema(DollarLineSchema):
    qualification = NameEnumField(atf.Qualification, required=True, allow_none=True)
    extent = fields.Function(
        lambda strict: StateDollarLineSchema.dump_extent(strict.extent),
        lambda value: value,
        required=True,
        allow_none=True,
    )
    scope = fields.Nested(ScopeContainerSchema, required=True, allow_none=True)
    state = NameEnumField(atf.State, required=True, allow_none=True)
    status = NameEnumField(atf.DollarStatus, required=True, allow_none=True)
    display_value = fields.String(data_key="displayValue")

    @post_load
    def make_line(self, data, **kwargs) -> StateDollarLine:
        return StateDollarLine(
            data["qualification"],
            StateDollarLineSchema.load_extent(data["extent"]),
            data["scope"],
            data["state"],
            data["status"],
        )

    @staticmethod
    def load_extent(extent):
        if isinstance(extent, str):
            return atf.Extent[extent]
        elif isinstance(extent, list):
            return tuple(extent)
        else:
            return extent

    @staticmethod
    def dump_extent(extent):
        if isinstance(extent, atf.Extent):
            return extent.name
        elif isinstance(extent, tuple):
            return list(extent)
        else:
            return extent
