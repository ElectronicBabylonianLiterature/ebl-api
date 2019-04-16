import attr
import pydash
import pytest
from ebl.auth0 import Guest
from ebl.tests.factories.corpus import TextFactory
from ebl.errors import NotFoundError, Defect


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


def test_creating_text(corpus,
                       text_repository,
                       bibliography,
                       changelog,
                       user,
                       when):
    # pylint: disable=R0913
    expect_validate_references(bibliography, when)
    when(changelog).create(
        COLLECTION,
        user.profile,
        {'_id': TEXT.id},
        {**TEXT.to_dict(), '_id': TEXT.id}
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
                       user,
                       when):
    # pylint: disable=R0913
    updated_text = attr.evolve(TEXT, index=TEXT.index + 1, name='New Name')
    dehydrated_updated_text = attr.evolve(
        DEHYDRATED_TEXT,
        index=DEHYDRATED_TEXT.index + 1,
        name='New Name'
    )
    when(text_repository).find(TEXT.id).thenReturn(DEHYDRATED_TEXT)
    (when(text_repository)
     .update(TEXT.id, updated_text)
     .thenReturn(dehydrated_updated_text))
    when(changelog).create(
        COLLECTION,
        user.profile,
        {**TEXT.to_dict(), '_id': TEXT.id},
        {**updated_text.to_dict(), '_id': updated_text.id}
    ).thenReturn()
    expect_validate_references(bibliography, when)
    expect_bibliography(bibliography, when)

    result = corpus.update(TEXT.id, updated_text, user)

    assert result == updated_text
