from marshmallow import fields, validate

from ebl.sumerian_dictionary.domain.sumerian_word import (
    AkkadianEquivalent,
    Attestation,
    AttingerForm,
    AttingerSense,
    Citation,
    EmesalForm,
    Epsd2Form,
    Epsd2Sense,
    Rendering,
    SignEntry,
    SignSpelling,
    UnrenderedToken,
)
from ebl.sumerian_dictionary.infrastructure.sumerian_schema_base import (
    ATTINGER_SOURCE,
    BORGER_SOURCE,
    DICTIONARY_SOURCES,
    RENDERING_KINDS,
    OPTIONAL_SIGN_LISTS,
    UNRENDERED_REASONS,
    AttrsSchema,
)


class AttingerSenseSchema(AttrsSchema):
    model = AttingerSense

    meaning = fields.String(required=True)
    lang = fields.String(required=True)
    entry_id = fields.String(required=True, data_key="entryId")


class Epsd2SenseSchema(AttrsSchema):
    model = Epsd2Sense

    num = fields.String(required=True)
    meaning = fields.String(required=True)
    lang = fields.String(required=True)


class AttingerFormSchema(AttrsSchema):
    model = AttingerForm

    spelling = fields.String(required=True)
    non_standard = fields.Boolean(required=True, data_key="nonStandard")
    attestations = fields.String(load_default="")


class Epsd2FormSchema(AttrsSchema):
    model = Epsd2Form

    spelling = fields.String(required=True)
    count = fields.Integer(required=True)
    percent = fields.Float(required=True)


class EmesalFormSchema(AttrsSchema):
    model = EmesalForm

    form = fields.String(required=True)
    source = fields.String(required=True, validate=validate.OneOf(ATTINGER_SOURCE))


class SignSpellingSchema(AttrsSchema):
    model = SignSpelling

    source = fields.String(required=True, validate=validate.OneOf(DICTIONARY_SOURCES))
    spelling = fields.String(required=True)


class SignEntrySchema(AttrsSchema):
    model = SignEntry

    reading = fields.String(required=True)
    name = fields.String(required=True)
    utf8 = fields.String(required=True)
    ambiguous = fields.Boolean(required=True)
    sources = fields.List(fields.Nested(SignSpellingSchema), required=True)
    sign_list = fields.String(
        data_key="signList",
        load_default="",
        validate=validate.OneOf(OPTIONAL_SIGN_LISTS),
    )
    character_list = fields.String(
        data_key="characterList",
        load_default="",
        validate=validate.OneOf(OPTIONAL_SIGN_LISTS),
    )
    known_wrong_character = fields.Boolean(
        data_key="knownWrongCharacter", load_default=False
    )
    determinative = fields.Boolean(load_default=False)
    unresolved = fields.Boolean(load_default=False)
    form_of = fields.List(fields.String(), data_key="formOf", load_default=list)


class UnrenderedTokenSchema(AttrsSchema):
    model = UnrenderedToken

    token = fields.String(required=True)
    reason = fields.String(required=True, validate=validate.OneOf(UNRENDERED_REASONS))


class RenderingSchema(AttrsSchema):
    model = Rendering

    spelling = fields.String(required=True)
    source = fields.String(required=True, validate=validate.OneOf(DICTIONARY_SOURCES))
    kind = fields.String(required=True, validate=validate.OneOf(RENDERING_KINDS))
    cuneiform = fields.List(fields.String(), required=True)
    complete = fields.Boolean(required=True)
    sign_lists = fields.List(fields.String(), data_key="signLists", load_default=list)
    unrendered = fields.List(fields.Nested(UnrenderedTokenSchema), load_default=list)
    printed = fields.String(load_default="")
    known_wrong_characters = fields.List(
        fields.String(), data_key="knownWrongCharacters", load_default=list
    )


class CitationSchema(AttrsSchema):
    model = Citation

    work = fields.String(required=True)
    passage = fields.String(load_default="")
    etcsl = fields.String(load_default="")
    composition_id = fields.String(data_key="compositionId", load_default="")


class AkkadianEquivalentSchema(AttrsSchema):
    model = AkkadianEquivalent

    word_id = fields.String(required=True, data_key="wordId")
    source = fields.String(required=True, validate=validate.OneOf(BORGER_SOURCE))
    index_numbers = fields.String(data_key="indexNumbers", load_default="")


class AttestationSchema(AttrsSchema):
    model = Attestation

    count = fields.Integer(load_default=0)
    periods = fields.List(fields.String(), load_default=list)
