from marshmallow import fields

from ebl.bibliography.application.reference_schema import ReferenceSchema
from ebl.corpus.application.display_schemas import ChapterDisplaySchema
from ebl.corpus.application.schemas import (
    ChapterSchema,
    DictionaryLineSchema,
    ManuscriptAttestationSchema,
    ManuscriptSchema,
)


class StoredManuscriptSchema(ManuscriptSchema):
    siglum_disambiguator = fields.String(
        load_default="", data_key="siglumDisambiguator"
    )
    accession = fields.String(load_default="")
    notes = fields.String(load_default="")
    references = fields.Nested(ReferenceSchema, many=True, load_default=())


class StoredChapterSchema(ChapterSchema):
    manuscripts = fields.Nested(StoredManuscriptSchema, many=True, required=True)


class StoredChapterDisplaySchema(ChapterDisplaySchema):
    manuscripts = fields.Nested(StoredManuscriptSchema, many=True, required=True)


class StoredDictionaryLineSchema(DictionaryLineSchema):
    manuscripts = fields.Nested(StoredManuscriptSchema, many=True, required=True)


class StoredManuscriptAttestationSchema(ManuscriptAttestationSchema):
    manuscript = fields.Nested(StoredManuscriptSchema, required=True)
