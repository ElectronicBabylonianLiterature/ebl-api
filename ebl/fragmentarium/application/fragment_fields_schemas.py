import pydash
from marshmallow import Schema, fields, post_dump, post_load, EXCLUDE
from ebl.fragmentarium.domain.folios import Folio, Folios
from ebl.fragmentarium.domain.fragment import (
    Acquisition,
    DossierReference,
    Introduction,
    Measure,
    Notes,
    Script,
    UncuratedReference,
)
from ebl.fragmentarium.domain.record import Record, RecordEntry, RecordType
from ebl.schemas import ValueEnumField
from ebl.transliteration.application.note_line_part_schemas import (
    OneOfNoteLinePartSchema,
)
from ebl.common.domain.period import Period, PeriodModifier
from ebl.fragmentarium.domain.fragment_external_numbers import ExternalNumbers


class AcquisitionSchema(Schema):
    description = fields.String()
    date = fields.Integer()
    supplier = fields.String(required=True)

    @post_load
    def make_acquisition(self, data, **kwargs):
        return Acquisition(**data)


class DossierReferenceSchema(Schema):
    dossierId = fields.String(required=True)
    isUncertain = fields.Boolean(load_default=False)

    @post_load
    def make_dossier_reference(self, data, **kwargs) -> DossierReference:
        return DossierReference(**data)


class ExternalNumbersSchema(Schema):
    cdli_number = fields.String(load_default="", data_key="cdliNumber")
    bm_id_number = fields.String(load_default="", data_key="bmIdNumber")
    archibab_number = fields.String(load_default="", data_key="archibabNumber")
    bdtns_number = fields.String(load_default="", data_key="bdtnsNumber")
    rsti_number = fields.String(load_default="", data_key="rstiNumber")
    chicago_isac_number = fields.String(load_default="", data_key="chicagoIsacNumber")
    ur_online_number = fields.String(load_default="", data_key="urOnlineNumber")
    hilprecht_jena_number = fields.String(
        load_default="", data_key="hilprechtJenaNumber"
    )
    hilprecht_heidelberg_number = fields.String(
        load_default="", data_key="hilprechtHeidelbergNumber"
    )
    metropolitan_number = fields.String(load_default="", data_key="metropolitanNumber")
    pierpont_morgan_number = fields.String(
        load_default="", data_key="pierpontMorganNumber"
    )
    yale_peabody_number = fields.String(load_default="", data_key="yalePeabodyNumber")
    louvre_number = fields.String(load_default="", data_key="louvreNumber")
    ontario_number = fields.String(load_default="", data_key="ontarioNumber")
    kelsey_number = fields.String(load_default="", data_key="kelseyNumber")
    harvard_ham_number = fields.String(load_default="", data_key="harvardHamNumber")
    sketchfab_number = fields.String(load_default="", data_key="sketchfabNumber")
    ark_number = fields.String(load_default="", data_key="arkNumber")
    dublin_tcd_number = fields.String(load_default="", data_key="dublinTcdNumber")
    cambridge_maa_number = fields.String(load_default="", data_key="cambridgeMaaNumber")
    ashmolean_number = fields.String(load_default="", data_key="ashmoleanNumber")
    alalah_hpm_number = fields.String(load_default="", data_key="alalahHpmNumber")
    philadelphia_number = fields.String(load_default="", data_key="philadelphiaNumber")
    australianinstituteofarchaeology_number = fields.String(
        load_default="", data_key="australianinstituteofarchaeologyNumber"
    )
    achemenet_number = fields.String(load_default="", data_key="achemenetNumber")
    nabucco_number = fields.String(load_default="", data_key="nabuccoNumber")
    oracc_numbers = fields.List(
        fields.String(), load_default=(), data_key="oraccNumbers"
    )
    digitale_keilschrift_bibliothek_number = fields.String(
        load_default="", data_key="digitaleKeilschriftBibliothekNumber"
    )
    seal_numbers = fields.List(fields.String(), load_default=(), data_key="sealNumbers")

    @post_load
    def make_external_numbers(self, data, **kwargs) -> ExternalNumbers:
        data["oracc_numbers"] = tuple(data["oracc_numbers"])
        data["seal_numbers"] = tuple(data["seal_numbers"])
        return ExternalNumbers(**data)

    @post_dump
    def omit_empty_numbers(self, data, **kwargs):
        return pydash.omit_by(data, pydash.is_empty)


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


class MarkupTextSchema(Schema):
    text = fields.String(required=True)
    parts = fields.List(fields.Nested(OneOfNoteLinePartSchema), required=True)


class IntroductionSchema(MarkupTextSchema):
    @post_load
    def make_introduction(self, data, **kwargs) -> Introduction:
        return Introduction(data["text"], tuple(data["parts"]))


class MeasureSchema(Schema):
    value = fields.Float(load_default=None)
    note = fields.String(load_default=None)

    @post_load
    def make_measure(self, data, **kwargs):
        return Measure(**data)

    @post_dump
    def filter_none(self, data, **kwargs):
        return pydash.omit_by(data, pydash.is_none)


class NotesSchema(MarkupTextSchema):
    @post_load
    def make_notes(self, data, **kwargs) -> Notes:
        return Notes(data["text"], tuple(data["parts"]))


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


class UncuratedReferenceSchema(Schema):
    document = fields.String(required=True)
    pages = fields.List(fields.Integer(), required=True)
    search_term = fields.String(data_key="searchTerm", allow_none=True)

    @post_load
    def make_uncurated_reference(self, data, **kwargs):
        data["pages"] = tuple(data["pages"])
        return UncuratedReference(**data)
