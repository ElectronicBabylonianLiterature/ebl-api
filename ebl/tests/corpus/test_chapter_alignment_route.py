import json
from typing import cast

import attr
import falcon
import pytest

from ebl.corpus.web.chapter_schemas import ApiChapterSchema
from ebl.tests.factories.corpus import ChapterFactory, TextFactory
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.sign_tokens import Logogram, Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Joiner
from ebl.transliteration.domain.word_tokens import AbstractWord, Word
from ebl.tests.corpus.support import allow_references, allow_signs, create_chapter_url


DTO = {
    "alignment": [
        [
            [
                {
                    "alignment": [
                        {
                            "value": "ku-[nu-ši]",
                            "alignment": 0,
                            "variant": "KU",
                            "type": "Word",
                            "language": "SUMERIAN",
                        }
                    ],
                    "omittedWords": [1],
                }
            ]
        ]
    ]
}


def test_updating_alignment_and_invalidate_chapter_display_cache(
    cached_client, bibliography, sign_repository, signs, text_repository
):
    allow_signs(signs, sign_repository)
    chapter = ChapterFactory.build()

    text = TextFactory.build(
        genre=chapter.text_id.genre,
        category=chapter.text_id.category,
        index=chapter.text_id.index,
    )
    text_repository.create(text)
    allow_references(chapter, bibliography)
    text_repository.create_chapter(chapter)
    alignment = 0
    omitted_words = (1,)
    updated_chapter = attr.evolve(
        chapter,
        lines=(
            attr.evolve(
                chapter.lines[0],
                variants=(
                    attr.evolve(
                        chapter.lines[0].variants[0],
                        manuscripts=(
                            attr.evolve(
                                chapter.lines[0].variants[0].manuscripts[0],
                                line=TextLine.of_iterable(
                                    chapter.lines[0]
                                    .variants[0]
                                    .manuscripts[0]
                                    .line.line_number,
                                    (
                                        Word.of(
                                            [
                                                Reading.of_name("ku"),
                                                Joiner.hyphen(),
                                                BrokenAway.open(),
                                                Reading.of_name("nu"),
                                                Joiner.hyphen(),
                                                Reading.of_name("ši"),
                                                BrokenAway.close(),
                                            ],
                                            alignment=alignment,
                                            variant=Word.of(
                                                [Logogram.of_name("KU")],
                                                language=Language.SUMERIAN,
                                            ),
                                        ),
                                    ),
                                ),
                                omitted_words=omitted_words,
                            ),
                        ),
                        reconstruction=tuple(
                            (
                                cast(
                                    AbstractWord,
                                    token,
                                ).set_has_omitted_alignment(True)
                                if index in omitted_words
                                else token
                            )
                            for index, token in enumerate(
                                chapter.lines[0].variants[0].reconstruction
                            )
                        ),
                    ),
                ),
            ),
        ),
    )

    expected_chapter = ApiChapterSchema().dump(updated_chapter)

    first_result = cached_client.simulate_get(create_chapter_url(chapter, "/display"))
    assert first_result.status == falcon.HTTP_OK

    post_result = cached_client.simulate_post(
        create_chapter_url(chapter, "/alignment"), body=json.dumps(DTO)
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == expected_chapter

    get_result = cached_client.simulate_get(create_chapter_url(chapter))

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == expected_chapter

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
        f"/texts/{chapter.text_id.genre.value}/"
        f"{chapter.text_id.category}/{chapter.text_id.index}/"
        f"chapters/invalid/unknown/alignment",
        body=json.dumps(DTO),
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


@pytest.mark.parametrize(
    "dto,expected_status",
    [
        ({"alignment": [[[]]]}, falcon.HTTP_UNPROCESSABLE_ENTITY),
        ({}, falcon.HTTP_BAD_REQUEST),
    ],
)
def test_updating_invalid_alignment(
    dto, expected_status, client, bibliography, sign_repository, signs, text_repository
):
    allow_signs(signs, sign_repository)
    chapter = ChapterFactory.build()
    allow_references(chapter, bibliography)
    text_repository.create_chapter(chapter)

    post_result = client.simulate_post(
        create_chapter_url(chapter, "/alignment"), body=json.dumps(dto)
    )

    assert post_result.status == expected_status
