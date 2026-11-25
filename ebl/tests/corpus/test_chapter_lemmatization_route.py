import json

import falcon
import pytest

from ebl.corpus.domain.chapter import Chapter
from ebl.tests.corpus.support import (
    allow_references,
    allow_signs,
    create_chapter_dto,
    create_chapter_url,
)
from ebl.tests.corpus.lemmatized_chapter_support import lemmatize_first_line
from ebl.tests.factories.corpus import ChapterFactory, TextFactory


DTO = {
    "lemmatization": [
        [
            {
                "reconstruction": [
                    {"value": "%n"},
                    {"value": "buāru", "uniqueLemma": ["aklu I"]},
                    {"value": "(|)"},
                    {"value": "["},
                    {"value": "..."},
                    {"value": "||"},
                    {"value": "...]-buāru#", "uniqueLemma": []},
                ],
                "manuscripts": [[{"value": "ku-[nu-ši]", "uniqueLemma": ["aklu I"]}]],
            }
        ]
    ]
}


def test_updating_lemmatization_invalidates_chapter_display_cache(
    cached_client, bibliography, sign_repository, signs, text_repository
):
    allow_signs(signs, sign_repository)
    chapter: Chapter = ChapterFactory.build()
    text = TextFactory.build(
        genre=chapter.text_id.genre,
        category=chapter.text_id.category,
        index=chapter.text_id.index,
    )
    text_repository.create(text)
    allow_references(chapter, bibliography)
    text_repository.create_chapter(chapter)
    first_result = cached_client.simulate_get(create_chapter_url(chapter, "/display"))
    assert first_result.status == falcon.HTTP_OK
    updated_chapter = lemmatize_first_line(chapter)

    expected = create_chapter_dto(updated_chapter)

    post_result = cached_client.simulate_post(
        create_chapter_url(chapter, "/lemmatization"), body=json.dumps(DTO)
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == expected

    get_result = cached_client.simulate_get(create_chapter_url(chapter))

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == expected

    second_result = cached_client.simulate_get(create_chapter_url(chapter, "/display"))
    assert second_result.status == falcon.HTTP_OK
    assert first_result.json != second_result.json


def test_updating_invalid_stage(
    client, bibliography, sign_repository, signs, text_repository
):
    allow_signs(signs, sign_repository)
    chapter = ChapterFactory.build()
    allow_references(chapter, bibliography)
    text_repository.create_chapter(chapter)

    post_result = client.simulate_post(
        f"/texts/{chapter.text_id.genre.value}"
        f"/{chapter.text_id.category}/{chapter.text_id.index}"
        "/chapters/invalid/any/lemmatization",
        body=json.dumps(DTO),
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


@pytest.mark.parametrize(
    "dto,expected_status",
    [
        ({"lemmatization": [[[]]]}, falcon.HTTP_BAD_REQUEST),
        ({}, falcon.HTTP_BAD_REQUEST),
    ],
)
def test_updating_invalid_lemmatization(dto, expected_status, client, stored_chapter):
    post_result = client.simulate_post(
        create_chapter_url(stored_chapter, "/lemmatization"), body=json.dumps(dto)
    )

    assert post_result.status == expected_status
