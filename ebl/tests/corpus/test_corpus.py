import attr
import pydash
import pytest

from ebl.corpus.text import Text
from ebl.corpus.text_serializer import TextSerializer
from ebl.auth0 import Guest
from ebl.errors import Defect, NotFoundError
from ebl.tests.factories.corpus import TextFactory
from ebl.fragment.transliteration import Transliteration

COLLECTION = 'texts'
TEXT = TextFactory.build()
DEHYDRATED_TEXT = attr.evolve(TEXT, chapters=tuple(
    attr.evolve(chapter, manuscripts=tuple(
        attr.evolve(manuscript, references=tuple(
            attr.evolve(
                reference,
                document=None
            )
            for reference in manuscript.references
        ))
        for manuscript in chapter.manuscripts
    ))
    for chapter in TEXT.chapters
))
ANY_USER = Guest()


def to_dict(text: Text) -> dict:
    return TextSerializer.serialize(text, False)


def expect_bibliography(bibliography, when):
    for chapter in TEXT.chapters:
        for manuscript in chapter.manuscripts:
            for reference in manuscript.references:
                (when(bibliography)
                 .find(reference.id)
                 .thenReturn(reference.document))


def expect_validate_references(bibliography, when):
    when(bibliography).validate_references(
        pydash
        .chain(TEXT.chapters)
        .flat_map(lambda chapter: chapter.manuscripts)
        .flat_map(lambda manuscript: manuscript.references)
        .value()
    ).thenReturn()


def expect_signs(sign_list, when):
    (pydash
     .chain(TEXT.chapters)
     .flat_map(lambda chapter: chapter.lines)
     .flat_map(lambda line: line.manuscripts)
     .map(lambda manuscript: manuscript.line.atf)
     .map(lambda atf: Transliteration(atf).cleaned)
     .for_each(lambda cleaned: when(sign_list)
               .map_transliteration(cleaned)
               .thenReturn([['X']]))
     .value())


def test_creating_text(corpus,
                       text_repository,
                       bibliography,
                       changelog,
                       sign_list,
                       user,
                       when):
    # pylint: disable=R0913
    expect_signs(sign_list, when)
    expect_validate_references(bibliography, when)
    when(changelog).create(
        COLLECTION,
        user.profile,
        {'_id': TEXT.id},
        {**to_dict(TEXT), '_id': TEXT.id}
    ).thenReturn()
    when(text_repository).create(TEXT).thenReturn()

    corpus.create(TEXT, user)


def test_finding_text(corpus, text_repository, bibliography, when):
    when(text_repository).find(TEXT.id).thenReturn(DEHYDRATED_TEXT)
    expect_bibliography(bibliography, when)

    assert corpus.find(TEXT.id) == TEXT


def test_find_raises_exception_if_references_not_found(corpus,
                                                       text_repository,
                                                       bibliography,
                                                       when):
    when(text_repository).find(TEXT.id).thenReturn(DEHYDRATED_TEXT)
    when(bibliography).find(...).thenRaise(NotFoundError())

    with pytest.raises(Defect):
        corpus.find(TEXT.id)


def test_updating_text(corpus,
                       text_repository,
                       bibliography,
                       changelog,
                       sign_list,
                       user,
                       when):
    # pylint: disable=R0913
    updated_text = attr.evolve(TEXT, index=TEXT.index + 1, name='New Name')
    dehydrated_updated_text = attr.evolve(
        DEHYDRATED_TEXT,
        index=DEHYDRATED_TEXT.index + 1,
        name='New Name'
    )
    expect_signs(sign_list, when)
    when(text_repository).find(TEXT.id).thenReturn(DEHYDRATED_TEXT)
    (when(text_repository)
     .update(TEXT.id, updated_text)
     .thenReturn(dehydrated_updated_text))
    when(changelog).create(
        COLLECTION,
        user.profile,
        {**to_dict(TEXT), '_id': TEXT.id},
        {**to_dict(updated_text), '_id': updated_text.id}
    ).thenReturn()
    expect_validate_references(bibliography, when)
    expect_bibliography(bibliography, when)

    result = corpus.update(TEXT.id, updated_text, user)

    assert result == updated_text
