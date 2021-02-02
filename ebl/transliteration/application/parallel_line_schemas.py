from marshmallow import fields, post_load  # pyre-ignore[21]

from ebl.fragmentarium.application.museum_number_schema import MuseumNumberSchema
from ebl.schemas import NameEnum
from ebl.transliteration.application.line_number_schemas import OneOfLineNumberSchema
from ebl.transliteration.application.line_schemas import LineBaseSchema
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.tokens import ValueToken
from ebl.transliteration.domain.parallel_line import ParallelFragment


class ParallelLineSchema(LineBaseSchema):
    prefix = fields.Constant("//")
    content = fields.Function(
        # pyre-ignore[16]
        lambda obj: [OneOfTokenSchema().dump(ValueToken.of(obj.display_value))],
        lambda value: value,
    )
    display_value = fields.String(data_key="displayValue")
    has_cf = fields.Boolean(data_key="hasCf", required=True)


class ParallelFragmentSchema(ParallelLineSchema):
    museum_number = fields.Nested(
        MuseumNumberSchema, required=True, data_key="museumNumber"
    )
    has_duplicates = fields.Boolean(data_key="hasDuplicates", required=True)
    surface = NameEnum(atf.Surface, required=True, allow_none=True)
    line_number = fields.Nested(
        OneOfLineNumberSchema, required=True, data_key="lineNumber"
    )

    @post_load  # pyre-ignore[56]
    def make_line(self, data, **kwargs) -> ParallelFragment:
        return ParallelFragment(
            data["has_cf"],
            data["museum_number"],
            data["has_duplicates"],
            data["surface"],
            data["line_number"],
        )
