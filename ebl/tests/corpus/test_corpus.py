import attr
import pydash
import pytest
from ebl.tests.factories.corpus import TextFactory
from ebl.errors import NotFoundError, DuplicateError


COLLECTION = 'texts'
TEXT = TextFactory.build()


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


def test_creating_text(database, corpus, bibliography, when):
    expect_validate_references(bibliography, when)
    corpus.create(TEXT)

    result = database[COLLECTION].find_one({
        'category': TEXT.category,
        'index': TEXT.index
    })
    assert pydash.omit(result, '_id') == TEXT.to_dict()


def test_it_is_not_possible_to_create_duplicates(corpus, bibliography, when):
    corpus.create_indexes()
    expect_validate_references(bibliography, when)
    corpus.create(TEXT)

    with pytest.raises(DuplicateError):
        corpus.create(TEXT)


def test_finding_text(database, corpus, bibliography, when):
    database[COLLECTION].insert_one(TEXT.to_dict())
    expect_bibliography(bibliography, when)

    assert corpus.find(TEXT.category, TEXT.index) == TEXT


def test_find_raises_exception_if_text_not_found(corpus):
    with pytest.raises(NotFoundError):
        corpus.find(1, 1)


def test_updating_text(database, corpus, bibliography, when):
    updated_text = attr.evolve(TEXT, index=TEXT.index + 1, name='New Name')
    database[COLLECTION].insert_one(TEXT.to_dict())
    expect_validate_references(bibliography, when)
    expect_bibliography(bibliography, when)

    result = corpus.update(TEXT.category, TEXT.index, updated_text)

    assert result == updated_text
    assert corpus.find(updated_text.category, updated_text.index) ==\
        updated_text


def test_updating_non_existing_text_raises_exception(corpus,
                                                     bibliography,
                                                     when):
    expect_validate_references(bibliography, when)
    with pytest.raises(NotFoundError):
        corpus.update(TEXT.category, TEXT.index, TEXT)
