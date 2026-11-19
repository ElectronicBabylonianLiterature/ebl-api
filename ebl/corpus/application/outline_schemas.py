from typing import Any, Mapping, cast

from marshmallow import Schema, fields, post_load

from ebl.corpus.application.id_schemas import TextIdSchema
from ebl.corpus.application.line_schemas import manuscript_id
from ebl.corpus.application.manuscript_schemas import ManuscriptSchema
from ebl.corpus.domain.chapter import Classification
from ebl.corpus.domain.chapter_outline import (
    ChapterOutline,
    LineOutline,
    LineVariantOutline,
    ManuscriptOutline,
    museum_number_to_string,
)
from ebl.corpus.domain.chapter_revision import LEGACY_REVISION
from ebl.corpus.domain.line_atf import reconstruction_to_atf, translation_to_atf
from ebl.corpus.domain.line_variant import prepare_reconstruction
from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.schemas import StageField, ValueEnumField
from ebl.transliteration.application.line_number_schemas import OneOfLineNumberSchema
from ebl.transliteration.application.line_schemas import (
    NoteLineSchema,
    TranslationLineSchema,
)
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.transliteration.application.one_of_line_schema import ParallelLineSchema
from ebl.transliteration.application.token_schemas import OneOfTokenSchema


class LineVariantOutlineDocumentSchema(Schema):
    reconstruction = fields.Nested(OneOfTokenSchema, required=True, many=True)
    note = fields.Nested(NoteLineSchema, required=True, allow_none=True)
    parallel_lines = fields.Nested(
        ParallelLineSchema, many=True, load_default=(), data_key="parallelLines"
    )
    manuscript_ids = fields.List(
        manuscript_id(), required=True, data_key="manuscriptIds"
    )

    @post_load
    def make_line_variant_outline(
        self, data: dict[str, Any], **kwargs: object
    ) -> LineVariantOutline:
        return LineVariantOutline(
            reconstruction_to_atf(
                prepare_reconstruction(tuple(data["reconstruction"])),
                data["note"],
                tuple(data["parallel_lines"]),
            ),
            tuple(data["manuscript_ids"]),
        )


class LineOutlineDocumentSchema(Schema):
    number = fields.Nested(OneOfLineNumberSchema, required=True)
    is_second_line_of_parallelism = fields.Boolean(
        required=True, data_key="isSecondLineOfParallelism"
    )
    is_beginning_of_section = fields.Boolean(
        required=True, data_key="isBeginningOfSection"
    )
    translation = fields.Nested(TranslationLineSchema, many=True, load_default=())
    variants = fields.Nested(LineVariantOutlineDocumentSchema, many=True, required=True)


def _make_line_outline(index: int, line: Mapping[str, Any]) -> LineOutline:
    return LineOutline(
        index,
        line["number"].label,
        line["is_second_line_of_parallelism"],
        line["is_beginning_of_section"],
        translation_to_atf(line["translation"]),
        tuple(line["variants"]),
    )


class ChapterOutlineDocumentSchema(Schema):
    text_id = fields.Nested(TextIdSchema, required=True, data_key="textId")
    classification = ValueEnumField(Classification, required=True)
    stage = StageField(required=True)
    version = fields.String(required=True)
    name = fields.String(required=True)
    order = fields.Integer(required=True)
    uncertain_fragments = fields.Nested(
        MuseumNumberSchema, many=True, load_default=(), data_key="uncertainFragments"
    )
    manuscripts = fields.Nested(ManuscriptSchema, many=True, required=True)
    lines = fields.Nested(LineOutlineDocumentSchema, many=True, required=True)
    revision = fields.String(load_default=LEGACY_REVISION)

    @post_load
    def make_chapter_outline(
        self, data: dict[str, Any], **kwargs: object
    ) -> ChapterOutline:
        return ChapterOutline(
            data["text_id"],
            data["classification"],
            data["stage"],
            data["version"],
            data["name"],
            data["order"],
            tuple(map(museum_number_to_string, data["uncertain_fragments"])),
            tuple(map(ManuscriptOutline.of_manuscript, data["manuscripts"])),
            tuple(
                _make_line_outline(index, line)
                for index, line in enumerate(data["lines"])
            ),
            data["revision"],
        )


def load_chapter_outline(
    document: Mapping[str, Any], provenance_service: ProvenanceService
) -> ChapterOutline:
    return cast(
        ChapterOutline,
        ChapterOutlineDocumentSchema(
            context={"provenance_service": provenance_service}
        ).load(document),
    )
