from typing import Union, Sequence
import attr
from marshmallow import Schema, fields, post_load
from ebl.bibliography.domain.reference import Reference
from ebl.corpus.domain.line import Line, ManuscriptLine
from ebl.corpus.domain.manuscript import Manuscript, OldSiglum
from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema
from ebl.corpus.application.schemas import ManuscriptLineSchema, labels
from ebl.corpus.web.chapter_schemas import ApiManuscriptSchema, ApiOldSiglumSchema
from ebl.bibliography.application.reference_schema import ApiReferenceSchema
from operator import attrgetter

from ebl.transliteration.domain.dollar_line import DollarLine
from ebl.transliteration.domain.line import EmptyLine
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.text_line import TextLine


def get_manuscript_field(field_name):
    return lambda line, context: attrgetter(field_name)(
        context["manuscripts"][line.manuscript_id]
    )


@attr.s(frozen=True, auto_attribs=True)
class ManuscriptLineDisplay:
    manuscript: Manuscript
    line: Union[TextLine, EmptyLine]
    old_sigla: Sequence[OldSiglum]
    references: Sequence[Reference]
    siglum_disambiguator: str
    period_modifier: str
    period: str
    provenance: str
    type: str
    labels: Sequence[str]
    paratext: Sequence[Union[DollarLine, NoteLine]]

    @classmethod
    def from_manuscript_line(
        cls, manuscript: Manuscript, manuscript_line: ManuscriptLine
    ):
        return cls(
            manuscript,
            manuscript_line.line,
            manuscript.old_sigla,
            manuscript.references,
            manuscript.siglum_disambiguator,
            manuscript.period_modifier.value,
            manuscript.period.long_name,
            manuscript.provenance.long_name,
            manuscript.type.long_name,
            [label.to_value() for label in manuscript_line.labels],
            manuscript_line.paratext,
        )


@attr.s(frozen=True, auto_attribs=True)
class VariantDisplay:
    manuscripts: Sequence[ManuscriptLineDisplay]

    @classmethod
    def from_line_variant(cls, line_variant, manuscripts_by_id):

        manuscript_line_displays = list()

        for manuscript_line in line_variant.manuscripts:
            FULL_MANUSCRIPT = manuscripts_by_id[manuscript_line.manuscript_id]
            manuscript_line_displays.append(
                ManuscriptLineDisplay.from_manuscript_line(
                    FULL_MANUSCRIPT, manuscript_line
                )
            )

        return cls(manuscripts=manuscript_line_displays)


@attr.s(frozen=True, auto_attribs=True)
class LineDetails:
    variants: Sequence[VariantDisplay]
    # old_line_number: str = ""

    @classmethod
    def from_line_manuscripts(cls, line: Line, manuscripts: Sequence[Manuscript]):
        MANUSCRIPTS_BY_ID = {m.id: m for m in manuscripts}

        variant_displays = [
            VariantDisplay.from_line_variant(v, MANUSCRIPTS_BY_ID)
            for v in line.variants
        ]

        return cls(variants=variant_displays)


class ManuscriptLineDisplaySchema(Schema):
    # line is a top level line (< variants < manuscripts[MLines])
    line = fields.Nested(OneOfLineSchema, required=True)
    manuscript = fields.Nested(ApiManuscriptSchema, required=True)
    old_sigla = fields.Nested(ApiOldSiglumSchema, many=True, data_key="oldSigla")
    references = fields.Nested(ApiReferenceSchema, many=True)
    siglum_disambiguator = fields.String(data_key="siglumDisambiguator")
    period_modifier = fields.String(data_key="periodModifier")
    period = fields.String()
    provenance = fields.String()
    type = fields.String()
    labels = fields.List(fields.String())
    paratext = fields.Nested(OneOfLineSchema, many=True, required=True)

    @post_load
    def make_manuscript_line_display(self, data, **kwargs) -> ManuscriptLineDisplay:
        return ManuscriptLineDisplay(**data)


class VariantDisplaySchema(Schema):
    manuscripts = fields.Nested(ManuscriptLineDisplaySchema, many=True, required=True)


class LineDetailsSchema(Schema):
    # Add old_line_number
    variants = fields.Nested(VariantDisplaySchema, many=True, required=True)
