from marshmallow import fields, Schema  # pyre-ignore
from marshmallow.validate import Length


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


class VowelSchema(Schema):  # pyre-ignore[11]
    value = fields.List(fields.String(), required=True)
    notes = notes()


class FormSchema(Schema):  # pyre-ignore[11]
    lemma = lemma()
    notes = notes()
    attested = attested()


class LogogramSchema(Schema):  # pyre-ignore[11]
    logogram = fields.List(fields.String(), required=True, validate=Length(1))
    notes = notes()


class DerivedSchema(Schema):  # pyre-ignore[11]
    lemma = lemma()
    notes = notes()
    homonym = homonym()


class DerivedFromSchema(Schema):  # pyre-ignore[11]
    lemma = fields.List(fields.String(), required=True)
    notes = notes()
    homonym = homonym()


class EntrySchema(Schema):  # pyre-ignore[11]
    meaning = meaning()
    vowels = fields.Nested(VowelSchema, many=True, required=True)


class AmplifiedMeaningSchema(Schema):  # pyre-ignore[11]
    key = fields.String(required=True)
    meaning = meaning()
    vowels = fields.Nested(VowelSchema, many=True, required=True)
    entries = fields.Nested(EntrySchema, many=True, required=True)


class OraccWordSchema(Schema):  # pyre-ignore[11]
    lemma = fields.String(required=True)
    guideWord = fields.String(required=True)


class WordSchema(Schema):  # pyre-ignore[11]
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
    derivedFrom = fields.Nested(DerivedSchema, required=True, allow_none=True)
    amplifiedMeanings = fields.Nested(AmplifiedMeaningSchema, required=True, many=True)
    source = fields.String()
    roots = fields.List(fields.String())
    pos = fields.List(fields.String(), required=True)
    guideWord = fields.String(validate=Length(1), required=True)
    oraccWords = fields.Nested(OraccWordSchema, required=True, many=True)
    origin = fields.String(required=True)
