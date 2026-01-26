from marshmallow import Schema, fields, post_load, validate

from ebl.corpus.application.id_schemas import TextIdSchema
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.schemas import NameEnumField, StageField
from ebl.transliteration.application.label_schemas import (
    ColumnLabelSchema,
    ObjectLabelSchema,
    SurfaceLabelSchema,
)
from ebl.transliteration.application.line_number_schemas import OneOfLineNumberSchema
from ebl.transliteration.application.line_schemas import LineBaseSchema
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain.parallel_line import (
    ChapterName,
    Labels,
    ParallelComposition,
    ParallelFragment,
    ParallelText,
)
from ebl.transliteration.domain.tokens import ValueToken
from ebl.transliteration.domain.genre import Genre


def exists() -> fields.Boolean:
    return fields.Boolean(allow_none=True, load_default=None)


class ParallelLineSchema(LineBaseSchema):
    prefix = fields.Constant("//")
    content = fields.Function(
        lambda obj: [OneOfTokenSchema().dump(ValueToken.of(obj.display_value))],
        lambda value: value,
    )
    display_value = fields.String(data_key="displayValue")
    has_cf = fields.Boolean(data_key="hasCf", required=True)


class LabelsSchema(Schema):
    object = fields.Nested(ObjectLabelSchema, allow_none=True, load_default=None)
    surface = fields.Nested(SurfaceLabelSchema, allow_none=True, load_default=None)
    column = fields.Nested(ColumnLabelSchema, allow_none=True, load_default=None)

    @post_load
    def make_labels(self, data, **kwargs) -> Labels:
        return Labels(
            data.get("object"),
            data.get("surface"),
            data.get("column"),
        )


class ParallelFragmentSchema(ParallelLineSchema):
    museum_number = fields.Nested(
        MuseumNumberSchema, required=True, data_key="museumNumber"
    )
    has_duplicates = fields.Boolean(data_key="hasDuplicates", required=True)
    labels = fields.Nested(LabelsSchema)
    surface = fields.Nested(
        SurfaceLabelSchema, allow_none=True, load_default=None, load_only=True
    )
    line_number = fields.Nested(
        OneOfLineNumberSchema, required=True, data_key="lineNumber"
    )
    exists = exists()

    @post_load
    def make_line(self, data, **kwargs) -> ParallelFragment:
        return ParallelFragment(
            data["has_cf"],
            data["museum_number"],
            data["has_duplicates"],
            data.get("labels", Labels(surface=data["surface"])),
            data["line_number"],
            data["exists"],
        )


class ChapterNameSchema(Schema):
    stage = StageField(required=True)
    version = fields.String(required=True)
    name = fields.String(required=True, validate=validate.Length(min=1))

    @post_load
    def make_id(self, data, **kwargs) -> ChapterName:
        return ChapterName(data["stage"], data["version"], data["name"])


class ParallelTextSchema(ParallelLineSchema):
    genre = NameEnumField(Genre, load_only=True)
    text = fields.Nested(TextIdSchema, required=True)
    chapter = fields.Nested(ChapterNameSchema, required=True, allow_none=True)
    line_number = fields.Nested(
        OneOfLineNumberSchema, required=True, data_key="lineNumber"
    )
    exists = exists()
    implicit_chapter = fields.Nested(
        ChapterNameSchema,
        load_default=None,
        allow_none=True,
        data_key="implicitChapter",
    )

    @post_load
    def make_line(self, data, **kwargs) -> ParallelText:
        return ParallelText(
            data["has_cf"],
            data["text"],
            data["chapter"],
            data["line_number"],
            data["exists"],
            data["implicit_chapter"],
        )


class ParallelCompositionSchema(ParallelLineSchema):
    name = fields.String(required=True)
    line_number = fields.Nested(
        OneOfLineNumberSchema, required=True, data_key="lineNumber"
    )

    @post_load
    def make_line(self, data, **kwargs) -> ParallelComposition:
        return ParallelComposition(data["has_cf"], data["name"], data["line_number"])
