from typing import Optional

from marshmallow import Schema, fields, post_load, EXCLUDE

from ebl.bibliography.application.reference_schema import ApiReferenceSchema
from ebl.bibliography.domain.reference import (
    BibliographyId,
    Reference,
    ReferenceType,
)
from ebl.realia.domain.realia_entry import (
    AfoCrossReference,
    AfoRegisterEntry,
    CrossReference,
    RealiaEntry,
    ReallexikonEntry,
)


class ReallexikonReferenceField(fields.Field):
    def _serialize(self, value, attr_name, obj, **kwargs):
        return None if value is None else ApiReferenceSchema().dump(value)

    def _deserialize(self, value, attr_name, data, **kwargs):
        if isinstance(value, str):
            return self._from_id(value, "")
        if isinstance(value, dict):
            return self._from_id(value.get("id", ""), value.get("pages", ""))
        return None

    def _from_id(self, bibliography_id: str, pages: str) -> Optional[Reference]:
        if not bibliography_id:
            return None
        return Reference(
            BibliographyId(bibliography_id), ReferenceType.DISCUSSION, pages=pages
        )


class CrossReferenceSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.String(required=True)
    lemma = fields.String(required=True)

    @post_load
    def make_entry(self, data, **kwargs) -> CrossReference:
        return CrossReference(**data)


class AfoCrossReferenceSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.String(required=True)
    lemma = fields.String(required=True)
    afo_volume = fields.String(data_key="afoVolume", required=True)
    page = fields.String(required=True)

    @post_load
    def make_entry(self, data, **kwargs) -> AfoCrossReference:
        return AfoCrossReference(**data)


class AfoRegisterEntrySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    main_word = fields.String(data_key="mainWord", load_default="")
    note = fields.String(load_default="")
    afo = fields.String(data_key="AfO", load_default="")
    reference = fields.String(load_default="")
    cross_reference = fields.String(data_key="crossReference", load_default="")
    afo_volume = fields.String(data_key="afoVolume", load_default="")
    page = fields.String(load_default="")
    cross_references = fields.List(
        fields.Nested(AfoCrossReferenceSchema),
        data_key="crossReferences",
        load_default=list,
    )

    @post_load
    def make_entry(self, data, **kwargs) -> AfoRegisterEntry:
        data["cross_references"] = tuple(data["cross_references"])
        return AfoRegisterEntry(**data)


class ReallexikonEntrySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.String(load_default="")
    title = fields.String(load_default="")
    reference = ReallexikonReferenceField(allow_none=True, load_default=None)

    @post_load
    def make_entry(self, data, **kwargs) -> ReallexikonEntry:
        return ReallexikonEntry(**data)


class RealiaEntrySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.String(required=True, data_key="_id")
    realia_id = fields.String(data_key="realiaId", load_default="")
    related_terms = fields.List(
        fields.String(), data_key="relatedTerms", load_default=list
    )
    type = fields.List(fields.String(), load_default=list)
    afo_register = fields.List(
        fields.Nested(AfoRegisterEntrySchema), data_key="afoRegister", load_default=list
    )
    references = fields.Nested(ApiReferenceSchema, many=True, load_default=list)
    wikidata_id = fields.List(fields.String(), data_key="wikidataId", load_default=list)
    reallexikon = fields.List(fields.Nested(ReallexikonEntrySchema), load_default=list)
    cross_references = fields.List(
        fields.Nested(CrossReferenceSchema),
        data_key="crossReferences",
        load_default=list,
    )
    afo_cross_references = fields.List(
        fields.Nested(AfoCrossReferenceSchema),
        data_key="afoCrossReferences",
        load_default=list,
    )

    @post_load
    def make_entry(self, data, **kwargs) -> RealiaEntry:
        data["related_terms"] = tuple(data["related_terms"])
        data["type"] = tuple(data["type"])
        data["afo_register"] = tuple(data["afo_register"])
        data["references"] = tuple(data["references"])
        data["wikidata_id"] = tuple(data["wikidata_id"])
        data["reallexikon"] = tuple(data["reallexikon"])
        data["cross_references"] = tuple(data["cross_references"])
        data["afo_cross_references"] = tuple(data["afo_cross_references"])
        return RealiaEntry(**data)
