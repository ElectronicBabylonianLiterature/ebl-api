from marshmallow import fields, Schema, pre_dump, post_load
from marshmallow.validate import Length

from ebl.schemas import ValueEnumField
from ebl.dictionary.domain.word import WordOrigin


def lemma():
    return fields.List(fields.String(), required=True, validate=Length(1))


def attested():
    return fields.Boolean(required=True)


def homonym():
    return fields.String(required=True)


def meaning():
    return fields.String(required=True)


def notes():
    return fields.List(fields.String(), required=True)


class VowelSchema(Schema):
    value = fields.List(fields.String(), required=True)
    notes = notes()


class FormSchema(Schema):
    lemma = lemma()
    notes = notes()
    attested = attested()


class LogogramSchema(Schema):
    logogram = fields.List(fields.String(), required=True, validate=Length(1))
    notes = notes()


class DerivedSchema(Schema):
    lemma = lemma()
    notes = notes()
    homonym = homonym()


class DerivedFromSchema(Schema):
    lemma = fields.List(fields.String(), required=True)
    notes = notes()
    homonym = homonym()


class EntrySchema(Schema):
    meaning = meaning()
    vowels = fields.Nested(VowelSchema, many=True, required=True)


class AmplifiedMeaningSchema(Schema):
    key = fields.String(required=True)
    meaning = meaning()
    vowels = fields.Nested(VowelSchema, many=True, required=True)
    entries = fields.Nested(EntrySchema, many=True, required=True)


class OraccWordSchema(Schema):
    lemma = fields.String(required=True)
    guideWord = fields.String(required=True)


class AkkadischeGlossareUndIndicesSchema(Schema):
    mainWord = fields.String(required=True)
    note = fields.String(required=True)
    reference = fields.String(required=True)
    AfO = fields.String(required=True)
    agiID = fields.String(required=True)


class WordSchema(Schema):
    _id = fields.String(required=True)
    lemma = lemma()
    homonym = homonym()
    attested = attested()
    legacyLemma = fields.String(required=True)
    forms = fields.Nested(FormSchema, required=True, many=True)
    meaning = meaning()
    logograms = fields.Nested(LogogramSchema, required=True, many=True)
    derived = fields.List(
        fields.List(fields.Nested(DerivedSchema), validate=Length(1)), required=True
    )
    derivedFrom = fields.Nested(DerivedFromSchema, required=True, allow_none=True)
    amplifiedMeanings = fields.Nested(AmplifiedMeaningSchema, required=True, many=True)
    source = fields.String()
    roots = fields.List(fields.String())
    pos = fields.List(fields.String(), required=True)
    guideWord = fields.String(validate=Length(1), required=True)
    arabicGuideWord = fields.String(required=True)
    oraccWords = fields.Nested(OraccWordSchema, required=True, many=True)
    akkadischeGlossareUndIndices = fields.Nested(
        AkkadischeGlossareUndIndicesSchema, load_default=None, many=True
    )
    cdaAddenda = fields.String()
    supplementsAkkadianDictionaries = fields.String()
    origin = ValueEnumField(WordOrigin, required=True)

    @pre_dump
    def _coerce_origin_for_dump(self, data, **kwargs):
        obj = dict(data) if isinstance(data, dict) else data
        origin = obj.get("origin") if isinstance(obj, dict) else None
        if isinstance(origin, str):
            obj["origin"] = WordOrigin(origin)
        return obj

    @post_load
    def _normalize_origin_after_load(self, data, **kwargs):
        origin = data.get("origin")
        if isinstance(origin, WordOrigin):
            data["origin"] = origin.value
        return data
