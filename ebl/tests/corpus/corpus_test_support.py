from dataclasses import dataclass
from itertools import chain
from typing import Any, cast

import attr
import pytest

from ebl.corpus.application.schemas import ChapterSchema
from ebl.corpus.domain.chapter import Chapter
from ebl.errors import NotFoundError
from ebl.tests.factories.corpus import ChapterFactory, TextFactory

CHAPTERS_COLLECTION = "chapters"
TEXT = TextFactory.build()
CHAPTER = ChapterFactory.build(text_id=TEXT.id)
CHAPTER_WITHOUT_DOCUMENTS = attr.evolve(
    CHAPTER,
    manuscripts=tuple(
        attr.evolve(
            manuscript,
            references=tuple(
                attr.evolve(reference, document=None)
                for reference in manuscript.references
            ),
        )
        for manuscript in CHAPTER.manuscripts
    ),
)


@dataclass(frozen=True)
class UpdateDependencies:
    text_repository: Any
    bibliography: Any
    changelog: Any
    signs: Any
    sign_repository: Any
    user: Any
    when: Any

    @classmethod
    def of(cls, request: pytest.FixtureRequest) -> "UpdateDependencies":
        return cls(
            text_repository=request.getfixturevalue("text_repository"),
            bibliography=request.getfixturevalue("bibliography"),
            changelog=request.getfixturevalue("changelog"),
            signs=request.getfixturevalue("signs"),
            sign_repository=request.getfixturevalue("sign_repository"),
            user=request.getfixturevalue("user"),
            when=request.getfixturevalue("when"),
        )


def expect_bibliography(bibliography, when) -> None:
    for manuscript in CHAPTER.manuscripts:
        for reference in chain(
            manuscript.references,
            (old_siglum.reference for old_siglum in manuscript.old_sigla),
        ):
            when(bibliography).find(reference.id).thenReturn(reference.document)


def expect_invalid_references(bibliography, when) -> None:
    when(bibliography).find(...).thenRaise(NotFoundError())


def expect_signs(signs, sign_repository) -> None:
    for sign in signs:
        sign_repository.create(sign)


def dump_chapter(chapter: Chapter) -> dict:
    return {**cast(dict, ChapterSchema().dump(chapter)), "_id": chapter.id_.to_tuple()}


def expect_chapter_update(
    dependencies: UpdateDependencies, old_chapter: Chapter, updated_chapter: Chapter
) -> None:
    expect_signs(dependencies.signs, dependencies.sign_repository)
    dependencies.when(dependencies.text_repository).update(
        CHAPTER.id_, updated_chapter
    ).thenReturn(updated_chapter)
    dependencies.when(dependencies.changelog).create(
        CHAPTERS_COLLECTION,
        dependencies.user.profile,
        dump_chapter(old_chapter),
        dump_chapter(updated_chapter),
    ).thenReturn()


def expect_find_and_update_chapter(
    dependencies: UpdateDependencies, old_chapter: Chapter, updated_chapter: Chapter
) -> None:
    dependencies.when(dependencies.text_repository).find_chapter(
        CHAPTER.id_
    ).thenReturn(old_chapter)
    expect_bibliography(dependencies.bibliography, dependencies.when)
    expect_chapter_update(dependencies, old_chapter, updated_chapter)
