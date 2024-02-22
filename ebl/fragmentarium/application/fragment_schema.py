import pydash
from ebl.schemas import NameEnumField
from marshmallow import Schema, fields, post_dump, post_load, EXCLUDE
from ebl.fragmentarium.domain.museum import Museum
from ebl.bibliography.application.reference_schema import ReferenceSchema
from ebl.common.application.schemas import AccessionSchema
from ebl.common.domain.period import Period, PeriodModifier
from ebl.fragmentarium.application.archaeology_schemas import ArchaeologySchema
from ebl.fragmentarium.application.genre_schema import GenreSchema
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.fragmentarium.domain.folios import Folio, Folios
from ebl.fragmentarium.domain.fragment import (
    Fragment,
    Introduction,
    Notes,
    Measure,
    Script,
    UncuratedReference,
    ExternalNumbers,
)
from ebl.fragmentarium.domain.line_to_vec_encoding import LineToVecEncoding
from ebl.fragmentarium.domain.record import Record, RecordEntry, RecordType
from ebl.schemas import ResearchProjectField, ScopeField, ValueEnumField
from ebl.transliteration.application.note_line_part_schemas import (
    OneOfNoteLinePartSchema,
)
from ebl.transliteration.application.text_schema import TextSchema
from ebl.fragmentarium.application.joins_schema import JoinsSchema
from ebl.fragmentarium.domain.joins import Joins
from ebl.fragmentarium.domain.date import DateSchema


class MeasureSchema(Schema):
    value = fields.Float(load_default=None)
    note = fields.String(load_default=None)

    @post_load
    def make_measure(self, data, **kwargs):
        return Measure(**data)

    @post_dump
    def filter_none(self, data, **kwargs):
        return pydash.omit_by(data, pydash.is_none)


class RecordEntrySchema(Schema):
    user = fields.String(required=True)
    type = ValueEnumField(RecordType, required=True)
    date = fields.String(required=True)

    @post_load
    def make_record_entry(self, data, **kwargs):
        return RecordEntry(**data)


class RecordSchema(Schema):
    entries = fields.Nested(RecordEntrySchema, many=True, required=True)

    @post_load
    def make_record(self, data, **kwargs):
        return Record(tuple(data["entries"]))


class FolioSchema(Schema):
    name = fields.String(required=True)
    number = fields.String(required=True)

    @post_load
    def make_record_entry(self, data, **kwargs):
        return Folio(**data)


class FoliosSchema(Schema):
    entries = fields.Nested(FolioSchema, many=True, required=True)

    @post_load
    def make_folio(self, data, **kwargs):
        return Folios(tuple(data["entries"]))


class UncuratedReferenceSchema(Schema):
    document = fields.String(required=True)
    pages = fields.List(fields.Integer(), required=True)

    @post_load
    def make_uncurated_reference(self, data, **kwargs):
        data["pages"] = tuple(data["pages"])
        return UncuratedReference(**data)


class MarkupTextSchema(Schema):
    text = fields.String(required=True)
    parts = fields.List(fields.Nested(OneOfNoteLinePartSchema), required=True)


class IntroductionSchema(MarkupTextSchema):
    @post_load
    def make_introduction(self, data, **kwargs) -> Introduction:
        return Introduction(data["text"], tuple(data["parts"]))


class NotesSchema(MarkupTextSchema):
    @post_load
    def make_notes(self, data, **kwargs) -> Notes:
        return Notes(data["text"], tuple(data["parts"]))


class ScriptSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    period = fields.Function(
        lambda script: script.period.long_name,
        lambda value: Period.from_name(value),
        required=True,
    )
    period_modifier = ValueEnumField(
        PeriodModifier, required=True, data_key="periodModifier"
    )
    uncertain = fields.Boolean(load_default=None)
    sort_key = fields.Function(
        lambda script: script.period.sort_key, data_key="sortKey", dump_only=True
    )

    @post_load
    def make_script(self, data, **kwargs) -> Script:
        return Script(**data)


class ExternalNumbersSchema(Schema):
    cdli_number = fields.String(load_default="", data_key="cdliNumber")
    bm_id_number = fields.String(load_default="", data_key="bmIdNumber")
    archibab_number = fields.String(load_default="", data_key="archibabNumber")
    bdtns_number = fields.String(load_default="", data_key="bdtnsNumber")
    ur_online_number = fields.String(load_default="", data_key="urOnlineNumber")
    hilprecht_jena_number = fields.String(
        load_default="", data_key="hilprechtJenaNumber"
    )
    hilprecht_heidelberg_number = fields.String(
        load_default="", data_key="hilprechtHeidelbergNumber"
    )
    metropolitan_number = fields.String(load_default="", data_key="metropolitanNumber")
    yale_peabody_number = fields.String(load_default="", data_key="yalePeabodyNumber")
    louvre_number = fields.String(load_default="", data_key="louvreNumber")
    alalah_hpm_number = fields.String(load_default="", data_key="alalahHpmNumber")
    philadelphia_number = fields.String(load_default="", data_key="philadelphiaNumber")
    australianinstituteofarchaeology_number = fields.String(
        load_default="", data_key="australianinstituteofarchaeologyNumber"
    )
    achemenet_number = fields.String(load_default="", data_key="achemenetNumber")
    nabucco_number = fields.String(load_default="", data_key="nabuccoNumber")
    oracc_numbers = fields.List(
        fields.String(), load_default=tuple(), data_key="oraccNumbers"
    )

    @post_load
    def make_external_numbers(self, data, **kwargs) -> ExternalNumbers:
        data["oracc_numbers"] = tuple(data["oracc_numbers"])
        return ExternalNumbers(**data)

    @post_dump
    def omit_empty_numbers(self, data, **kwargs):
        return pydash.omit_by(data, pydash.is_empty)


class FragmentSchema(Schema):
    number = fields.Nested(MuseumNumberSchema, required=True, data_key="museumNumber")
    accession = fields.Nested(AccessionSchema, allow_none=True, load_default=None)
    publication = fields.String(required=True)
    description = fields.String(required=True)
    collection = fields.String(required=True)
    legacy_script = fields.String(data_key="legacyScript", load_default="")
    traditional_references = fields.List(
        fields.String(), data_key="traditionalReferences"
    )
    museum = NameEnumField(Museum, required=True)
    width = fields.Nested(MeasureSchema, required=True)
    length = fields.Nested(MeasureSchema, required=True)
    thickness = fields.Nested(MeasureSchema, required=True)
    joins = fields.Pluck(JoinsSchema, "fragments", load_default=Joins())
    record = fields.Pluck(RecordSchema, "entries")
    folios = fields.Pluck(FoliosSchema, "entries")
    text = fields.Nested(TextSchema)
    signs = fields.String(load_default="")
    notes = fields.Nested(NotesSchema, default=Notes())
    references = fields.Nested(ReferenceSchema, many=True, required=True)
    uncurated_references = fields.Nested(
        UncuratedReferenceSchema,
        many=True,
        data_key="uncuratedReferences",
        load_default=None,
    )
    genres = fields.Nested(GenreSchema, many=True, load_default=tuple())
    line_to_vec = fields.List(
        fields.List(ValueEnumField(LineToVecEncoding)),
        load_default=tuple(),
        data_key="lineToVec",
    )
    authorized_scopes = fields.List(
        ScopeField(),
        data_key="authorizedScopes",
    )
    introduction = fields.Nested(IntroductionSchema, default=Introduction())
    script = fields.Nested(ScriptSchema, load_default=Script())
    external_numbers = fields.Nested(
        ExternalNumbersSchema,
        load_default=ExternalNumbers(),
        data_key="externalNumbers",
    )
    projects = fields.List(ResearchProjectField())
    date = fields.Nested(DateSchema, allow_none=True, default=None)
    dates_in_text = fields.Nested(
        DateSchema, data_key="datesInText", many=True, allow_none=True, default=list()
    )
    archaeology = fields.Nested(ArchaeologySchema, allow_none=True, default=None)

    @post_load
    def make_fragment(self, data, **kwargs):
        data["references"] = tuple(data["references"])
        data["genres"] = tuple(data["genres"])
        data["line_to_vec"] = tuple(map(tuple, data["line_to_vec"]))
        if "projects" in data:
            data["projects"] = tuple(data["projects"])
        if data["uncurated_references"] is not None:
            data["uncurated_references"] = tuple(data["uncurated_references"])
        if "authorized_scopes" in data:
            data["authorized_scopes"] = list(data["authorized_scopes"])
        if "dates_in_text" in data:
            data["dates_in_text"] = list(data["dates_in_text"])

        return Fragment(**data)

    @post_dump
    def filter_none(self, data, **kwargs):
        scope = data.get("authorizedScopes")
        if scope is not None and len(scope) == 0:
            data.pop("authorizedScopes")
        return pydash.omit_by(data, pydash.is_none)
