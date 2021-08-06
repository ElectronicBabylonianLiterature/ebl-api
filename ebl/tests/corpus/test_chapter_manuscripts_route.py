import json

import attr
import falcon
import pytest

from ebl.bibliography.application.reference_schema import ReferenceSchema
from ebl.corpus.domain.manuscript import (
    ManuscriptType,
    Period,
    PeriodModifier,
    Provenance,
)
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.corpus import ChapterFactory
from ebl.corpus.domain.stage import Stage
from ebl.tests.corpus.support import (
    allow_references,
    allow_signs,
    create_chapter_dto,
    create_chapter_url,
)


def test_updating(client, bibliography, sign_repository, signs, text_repository):
    uncertain_fragment = MuseumNumber.of("K.1")
    allow_signs(signs, sign_repository)
    chapter = ChapterFactory.build()
    allow_references(chapter, bibliography)
    text_repository.create_chapter(chapter)
    updated_chapter = attr.evolve(
        chapter,
        manuscripts=(
            attr.evolve(
                chapter.manuscripts[0], museum_number="new.number", accession=""
            ),
        ),
        uncertain_fragments=(uncertain_fragment,),
    )

    post_result = client.simulate_post(
        create_chapter_url(chapter, "/manuscripts"),
        body=json.dumps(
            {
                "manuscripts": create_chapter_dto(updated_chapter)["manuscripts"],
                "uncertainFragments": [str(uncertain_fragment)],
            }
        ),
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.headers["Access-Control-Allow-Origin"] == "*"
    assert post_result.json == create_chapter_dto(updated_chapter)

    get_result = client.simulate_get(create_chapter_url(chapter))

    assert get_result.status == falcon.HTTP_OK
    assert get_result.headers["Access-Control-Allow-Origin"] == "*"
    assert get_result.json == create_chapter_dto(updated_chapter)


def test_updating_text_not_found(client, bibliography):
    post_result = client.simulate_post(
        f"/texts/1/1/chapters/{Stage.STANDARD_BABYLONIAN.value}/unknown/manuscripts",
        body=json.dumps({"manuscripts": [], "uncertainFragments": []}),
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_updating_invalid_reference(
    client, bibliography, sign_repository, signs, text_repository
):
    allow_signs(signs, sign_repository)
    chapter = ChapterFactory.build()
    allow_references(chapter, bibliography)
    text_repository.create_chapter(chapter)
    manuscript = {
        "id": chapter.manuscripts[0].id,
        "siglumDisambiguator": "1c",
        "museumNumber": "X.1",
        "accession": "",
        "periodModifier": PeriodModifier.NONE.value,
        "period": Period.OLD_ASSYRIAN.long_name,
        "provenance": Provenance.BABYLON.long_name,
        "type": ManuscriptType.SCHOOL.long_name,
        "notes": "",
        "colophon": "",
        "unplacedLines": "",
        "references": [ReferenceSchema().dump(ReferenceFactory.build())],
    }

    post_result = client.simulate_post(
        create_chapter_url(chapter, "/manuscripts"),
        body=json.dumps({"manuscripts": [manuscript], "uncertainFragments": []}),
    )

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_updating_text_category(client):
    post_result = client.simulate_post(
        f"/texts/invalid/1/chapters/{Stage.STANDARD_BABYLONIAN.value}/unknown/manuscripts",
        body=json.dumps({"manuscripts": [], "uncertainFragments": []}),
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_updating_invalid_id(client):
    post_result = client.simulate_post(
        f"/texts/1/invalid/chapters/{Stage.STANDARD_BABYLONIAN.value}/unknown/manuscripts",
        body=json.dumps({"manuscripts": [], "uncertainFragments": []}),
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_updating_invalid_stage(client):
    post_result = client.simulate_post(
        "/texts/1/1/chapters/invalid/unknown/manuscripts",
        body=json.dumps({"manuscripts": [], "uncertainFragments": []}),
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


AMBIGUOUS_MANUSCRIPTS = {
    "manuscripts": [
        {
            "id": 1,
            "siglumDisambiguator": "1c",
            "museumNumber": "X.1",
            "accession": "",
            "periodModifier": PeriodModifier.NONE.value,
            "period": Period.OLD_ASSYRIAN.long_name,
            "provenance": Provenance.BABYLON.long_name,
            "type": ManuscriptType.SCHOOL.long_name,
            "notes": "",
            "colophon": "",
            "unplacedLines": "",
            "references": [],
        },
        {
            "id": 2,
            "siglumDisambiguator": "1c",
            "museumNumber": "X.2",
            "accession": "",
            "periodModifier": PeriodModifier.NONE.value,
            "period": Period.OLD_ASSYRIAN.long_name,
            "provenance": Provenance.BABYLON.long_name,
            "type": ManuscriptType.SCHOOL.long_name,
            "notes": "",
            "colophon": "",
            "unplacedLines": "",
            "references": [],
        },
    ],
    "uncertainFragments": [],
}


INVALID_MUSEUM_NUMBER = {
    "manuscripts": [
        {
            "id": 1,
            "siglumDisambiguator": "1c",
            "museumNumber": "invalid",
            "accession": "",
            "periodModifier": PeriodModifier.NONE.value,
            "period": Period.OLD_ASSYRIAN.long_name,
            "provenance": Provenance.BABYLON.long_name,
            "type": ManuscriptType.SCHOOL.long_name,
            "notes": "",
            "colophon": "",
            "unplacedLines": "",
            "references": [],
        }
    ],
    "uncertainFragments": [],
}


INVALID_PROVENANCE = {
    "manuscripts": [
        {
            "id": 1,
            "siglumDisambiguator": "1c",
            "museumNumber": "invalid",
            "accession": "",
            "periodModifier": PeriodModifier.NONE.value,
            "period": Period.OLD_ASSYRIAN.long_name,
            "provenance": Provenance.STANDARD_TEXT.long_name,
            "type": ManuscriptType.NONE.long_name,
            "notes": "",
            "colophon": "",
            "unplacedLines": "",
            "references": [],
        }
    ],
    "uncertainFragments": [],
}


@pytest.mark.parametrize(
    "manuscripts,expected_status",
    [
        [[{}], falcon.HTTP_BAD_REQUEST],
        [[], falcon.HTTP_UNPROCESSABLE_ENTITY],
        [AMBIGUOUS_MANUSCRIPTS, falcon.HTTP_BAD_REQUEST],
        [INVALID_MUSEUM_NUMBER, falcon.HTTP_BAD_REQUEST],
        [INVALID_PROVENANCE, falcon.HTTP_BAD_REQUEST],
        [
            {"manuscripts": [], "uncertainFragments": ["invalid"]},
            falcon.HTTP_BAD_REQUEST,
        ],
    ],
)
def test_update_invalid_entity(
    client,
    bibliography,
    manuscripts,
    expected_status,
    sign_repository,
    signs,
    text_repository,
):
    allow_signs(signs, sign_repository)
    chapter = ChapterFactory.build()
    allow_references(chapter, bibliography)
    text_repository.create_chapter(chapter)

    post_result = client.simulate_post(
        create_chapter_url(chapter, "/manuscripts"),
        body=json.dumps({"manuscripts": manuscripts, "uncertainFragments": []}),
    )

    assert post_result.status == expected_status
