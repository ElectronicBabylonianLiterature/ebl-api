import attr
from ebl.fragmentarium.application.named_entity_schema import NamedEntitySchema
import pydash
import pytest
from ebl.common.application.schemas import AccessionSchema

from ebl.errors import DataError
from ebl.fragmentarium.application.archaeology_schemas import ArchaeologySchema
from ebl.fragmentarium.application.fragment_info_schema import ApiFragmentInfoSchema
from ebl.fragmentarium.application.genre_schema import GenreSchema
from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.fragmentarium.domain.record import RecordType
from ebl.fragmentarium.web.dtos import create_response_dto, parse_museum_number
from ebl.tests.factories.fragment import (
    JoinFactory,
    LemmatizedFragmentFactory,
)
from ebl.transliteration.application.text_schema import TextSchema
from ebl.fragmentarium.application.fragment_fields_schemas import (
    AcquisitionSchema,
    DossierReferenceSchema,
    ExternalNumbersSchema,
    IntroductionSchema,
    NotesSchema,
    ScriptSchema,
)
from ebl.fragmentarium.application.joins_schema import JoinsSchema
from ebl.fragmentarium.application.colophon_schema import ColophonSchema
from ebl.fragmentarium.domain.date import DateSchema
from ebl.fragmentarium.domain.joins import Joins
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.common.domain.project import ResearchProject


@pytest.fixture
def lemmatized_fragment() -> Fragment:
    return LemmatizedFragmentFactory.build(joins=Joins(((JoinFactory.build(),),)))


@pytest.fixture
def has_photo():
    return True


@pytest.fixture
def expected_dto(lemmatized_fragment, has_photo):
    return pydash.omit_by(
        {
            "museumNumber": attr.asdict(lemmatized_fragment.number),
            "accession": AccessionSchema().dump(lemmatized_fragment.accession),
            "publication": lemmatized_fragment.publication,
            "cdliImages": lemmatized_fragment.cdli_images,
            "acquisition": AcquisitionSchema().dump(lemmatized_fragment.acquisition),
            "description": lemmatized_fragment.description,
            "joins": JoinsSchema().dump(lemmatized_fragment.joins)["fragments"],
            "length": attr.asdict(
                lemmatized_fragment.length, filter=lambda _, value: value is not None
            ),
            "width": attr.asdict(
                lemmatized_fragment.width, filter=lambda _, value: value is not None
            ),
            "thickness": attr.asdict(
                lemmatized_fragment.thickness, filter=lambda _, value: value is not None
            ),
            "collection": lemmatized_fragment.collection,
            "legacyScript": lemmatized_fragment.legacy_script,
            "traditionalReferences": lemmatized_fragment.traditional_references,
            "script": ScriptSchema().dump(lemmatized_fragment.script),
            "date": DateSchema().dump(lemmatized_fragment.date),
            "datesInText": [
                DateSchema().dump(date) for date in lemmatized_fragment.dates_in_text
            ],
            "notes": NotesSchema().dump(lemmatized_fragment.notes),
            "museum": lemmatized_fragment.museum.name,
            "signs": lemmatized_fragment.signs,
            "record": [
                {"user": entry.user, "type": entry.type.value, "date": entry.date}
                for entry in lemmatized_fragment.record.entries
            ],
            "folios": [
                attr.asdict(folio) for folio in lemmatized_fragment.folios.entries
            ],
            "text": TextSchema().dump(lemmatized_fragment.text),
            "references": [
                {
                    "id": reference.id,
                    "type": reference.type.name,
                    "pages": reference.pages,
                    "notes": reference.notes,
                    "linesCited": list(reference.lines_cited),
                }
                for reference in lemmatized_fragment.references
            ],
            "uncuratedReferences": (
                [
                    attr.asdict(reference)
                    for reference in lemmatized_fragment.uncurated_references
                ]
                if lemmatized_fragment.uncurated_references is not None
                else None
            ),
            "atf": lemmatized_fragment.text.atf,
            "hasPhoto": has_photo,
            "genres": [
                {"category": genre.category, "uncertain": genre.uncertain}
                for genre in lemmatized_fragment.genres
            ],
            "lineToVec": [
                [
                    line_to_vec_encoding.value
                    for line_to_vec_encoding in line_to_vec_encodings
                ]
                for line_to_vec_encodings in lemmatized_fragment.line_to_vec
            ],
            "introduction": IntroductionSchema().dump(lemmatized_fragment.introduction),
            "externalNumbers": ExternalNumbersSchema().dump(
                lemmatized_fragment.external_numbers
            ),
            "projects": [
                ResearchProject["CAIC"].abbreviation,
                ResearchProject["ALU_GENEVA"].abbreviation,
                ResearchProject["AMPS"].abbreviation,
                ResearchProject["RECC"].abbreviation,
            ],
            "archaeology": ArchaeologySchema().dump(lemmatized_fragment.archaeology),
            "colophon": ColophonSchema().dump(lemmatized_fragment.colophon),
            "authorizedScopes": [],
            "ocredSigns": "ABZ10 X",
            "dossiers": [
                DossierReferenceSchema().dump(dossier)
                for dossier in lemmatized_fragment.dossiers
            ],
            "namedEntities": NamedEntitySchema().dump(
                lemmatized_fragment.named_entities, many=True
            ),
        },
        pydash.is_none,
    )


def test_create_response_dto(user, lemmatized_fragment, expected_dto, has_photo):
    assert create_response_dto(lemmatized_fragment, user, has_photo) == expected_dto


def test_create_fragment_info_dto():
    lemmatized_fragment = LemmatizedFragmentFactory.build()
    text = parse_atf_lark("1. kur")
    info = FragmentInfo.of(lemmatized_fragment, text)
    record_entry = lemmatized_fragment.record.entries[0]
    is_transliteration = record_entry.type == RecordType.TRANSLITERATION
    assert ApiFragmentInfoSchema().dump(info) == {
        "number": str(info.number),
        "accession": AccessionSchema().dump(info.accession),
        "script": ScriptSchema().dump(info.script),
        "description": info.description,
        "acquisition": AcquisitionSchema().dump(info.acquisition),
        "matchingLines": TextSchema().dump(text),
        "editor": record_entry.user if is_transliteration else "",
        "editionDate": record_entry.date if is_transliteration else "",
        "references": [],
        "genres": GenreSchema().dump(lemmatized_fragment.genres, many=True),
    }


def test_parse_museum_number():
    number = MuseumNumber("A", "B", "C")
    assert parse_museum_number(str(number)) == number


def test_parse_invalid_museum_number():
    with pytest.raises(DataError):
        parse_museum_number("invalid")
