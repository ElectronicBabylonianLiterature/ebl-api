import attr
import pydash
import pytest
from ebl.auth0 import Guest
from ebl.tests.factories.corpus import TextFactory
from ebl.errors import NotFoundError, DuplicateError, Defect


COLLECTION = 'texts'
TEXT = TextFactory.build()
ANY_USER = Guest()


def when_text_in_collection(database):
    database[COLLECTION].insert_one(TEXT.to_dict())


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


def test_creating_text(database, corpus, bibliography, changelog, user, when):
    # pylint: disable=R0913
    expect_validate_references(bibliography, when)
    when(changelog).create(
        COLLECTION,
        user.profile,
        {'_id': TEXT.id},
        {**TEXT.to_dict(), '_id': TEXT.id}
    ).thenReturn()

    corpus.create(TEXT, user)

    result = database[COLLECTION].find_one({
        'category': TEXT.category,
        'index': TEXT.index
    })
    assert pydash.omit(result, '_id') == TEXT.to_dict()


def test_it_is_not_possible_to_create_duplicates(corpus,
                                                 bibliography,
                                                 when):
    corpus.create_indexes()
    expect_validate_references(bibliography, when)
    corpus.create(TEXT, ANY_USER)

    with pytest.raises(DuplicateError):
        corpus.create(TEXT, ANY_USER)


def test_finding_text(database, corpus, bibliography, when):
    when_text_in_collection(database)
    expect_bibliography(bibliography, when)

    assert corpus.find(TEXT.category, TEXT.index) == TEXT


def test_find_raises_exception_if_text_not_found(corpus):
    with pytest.raises(NotFoundError):
        corpus.find(1, 1)


def test_find_raises_exception_if_references_not_found(database,
                                                       corpus,
                                                       bibliography,
                                                       when):
    when_text_in_collection(database)
    when(bibliography).find(...).thenRaise(NotFoundError())
    with pytest.raises(Defect):
        corpus.find(TEXT.category, TEXT.index)


def test_updating_text(database, corpus, bibliography, changelog, user, when):
    # pylint: disable=R0913
    updated_text = attr.evolve(TEXT, index=TEXT.index + 1, name='New Name')
    when_text_in_collection(database)
    when(changelog).create(
        COLLECTION,
        user.profile,
        {**TEXT.to_dict(), '_id': TEXT.id},
        {**updated_text.to_dict(), '_id': updated_text.id}
    ).thenReturn()
    expect_validate_references(bibliography, when)
    expect_bibliography(bibliography, when)

    result = corpus.update(TEXT.category, TEXT.index, updated_text, user)

    assert result == updated_text
    assert corpus.find(updated_text.category, updated_text.index) ==\
        updated_text


def test_updating_non_existing_text_raises_exception(corpus,
                                                     bibliography,
                                                     when):
    expect_validate_references(bibliography, when)
    with pytest.raises(NotFoundError):
        corpus.update(TEXT.category, TEXT.index, TEXT, ANY_USER)
