import pydash
from ebl.fragmentarium.application.named_entity_schema import NamedEntitySchema
from ebl.schemas import NameEnumField
from marshmallow import Schema, fields, post_dump, post_load
from ebl.fragmentarium.domain.museum import Museum
from ebl.bibliography.application.reference_schema import ReferenceSchema
from ebl.common.application.schemas import AccessionSchema
from ebl.fragmentarium.application.archaeology_schemas import ArchaeologySchema
from ebl.fragmentarium.application.genre_schema import GenreSchema
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.fragmentarium.domain.fragment import (
    Fragment,
    Introduction,
    Notes,
    Script,
)
from ebl.fragmentarium.domain.fragment_external_numbers import ExternalNumbers
from ebl.fragmentarium.domain.line_to_vec_encoding import LineToVecEncoding
from ebl.schemas import ResearchProjectField, ScopeField, ValueEnumField
from ebl.transliteration.application.text_schema import TextSchema
from ebl.fragmentarium.application.joins_schema import JoinsSchema
from ebl.fragmentarium.domain.joins import Joins
from ebl.fragmentarium.domain.date import DateSchema
from ebl.fragmentarium.application.colophon_schema import ColophonSchema
from ebl.fragmentarium.application.fragment_fields_schemas import (
    AcquisitionSchema,
    DossierReferenceSchema,
    ExternalNumbersSchema,
    FoliosSchema,
    IntroductionSchema,
    MeasureSchema,
    NotesSchema,
    RecordSchema,
    ScriptSchema,
    UncuratedReferenceSchema,
)


class FragmentSchema(Schema):
    number = fields.Nested(MuseumNumberSchema, required=True, data_key="museumNumber")
    accession = fields.Nested(AccessionSchema, allow_none=True, load_default=None)
    publication = fields.String(required=True)
    acquisition = fields.Nested(AcquisitionSchema, allow_none=True, load_default=None)
    description = fields.String(required=True)
    cdli_images = fields.List(fields.String(), data_key="cdliImages")
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
    genres = fields.Nested(GenreSchema, many=True, load_default=())
    line_to_vec = fields.List(
        fields.List(ValueEnumField(LineToVecEncoding)),
        load_default=(),
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
        DateSchema, data_key="datesInText", many=True, allow_none=True, default=[]
    )
    archaeology = fields.Nested(ArchaeologySchema, allow_none=True, default=None)
    colophon = fields.Nested(ColophonSchema, allow_none=True, default=None)
    dossiers = fields.Nested(DossierReferenceSchema, many=True, default=[])
    named_entities = fields.Nested(
        NamedEntitySchema,
        many=True,
        default=(),
        data_key="namedEntities",
    )

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
    def filter_none(self, data, **kwargs) -> dict:
        return pydash.omit_by(data, pydash.is_none)
