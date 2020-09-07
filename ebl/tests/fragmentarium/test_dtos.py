import attr
import pydash  # pyre-ignore

from ebl.fragmentarium.application.fragment_info_schema import FragmentInfoSchema
from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.fragmentarium.domain.record import RecordType
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import LemmatizedFragmentFactory
from ebl.transliteration.application.text_schema import TextSchema


def test_create_response_dto(user):
    lemmatized_fragment = LemmatizedFragmentFactory.build()
    has_photo = True
    assert create_response_dto(lemmatized_fragment, user, has_photo) == pydash.omit_by(
        {
            "_id": str(lemmatized_fragment.number),
            "museumNumber": attr.asdict(lemmatized_fragment.number),
            "accession": lemmatized_fragment.accession,
            "cdliNumber": lemmatized_fragment.cdli_number,
            "bmIdNumber": lemmatized_fragment.bm_id_number,
            "publication": lemmatized_fragment.publication,
            "description": lemmatized_fragment.description,
            "joins": list(lemmatized_fragment.joins),
            "length": attr.asdict(
                lemmatized_fragment.length, filter=lambda _, value: value is not None,
            ),
            "width": attr.asdict(
                lemmatized_fragment.width, filter=lambda _, value: value is not None,
            ),
            "thickness": attr.asdict(
                lemmatized_fragment.thickness,
                filter=lambda _, value: value is not None,
            ),
            "collection": lemmatized_fragment.collection,
            "script": lemmatized_fragment.script,
            "notes": lemmatized_fragment.notes,
            "museum": lemmatized_fragment.museum,
            "signs": lemmatized_fragment.signs,
            "record": [
                {"user": entry.user, "type": entry.type.value, "date": entry.date,}
                for entry in lemmatized_fragment.record.entries
            ],
            "folios": [
                attr.asdict(folio)
                for folio in lemmatized_fragment.folios.filter(user).entries
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
        },
        pydash.is_none,
    )


def test_create_fragment_info_dto():
    lemmatized_fragment = LemmatizedFragmentFactory.build()
    line = "1. kur"
    info = FragmentInfo.of(lemmatized_fragment, ((line,),))
    record_entry = lemmatized_fragment.record.entries[0]
    is_transliteration = record_entry.type == RecordType.TRANSLITERATION
    assert FragmentInfoSchema().dump(info) == {
        "number": info.number,
        "accession": info.accession,
        "script": info.script,
        "description": info.description,
        "matchingLines": [[line]],
        "editor": record_entry.user if is_transliteration else "",
        "editionDate": record_entry.date if is_transliteration else "",
        "references": [],
    }
