import attr
import pydash
import pytest

from ebl.corpus.alignment import Alignment, AlignmentToken, AlignmentError
from ebl.corpus.text import Text
from ebl.corpus.text_serializer import TextSerializer
from ebl.auth0 import Guest
from ebl.errors import Defect, NotFoundError, DataError
from ebl.tests.factories.corpus import TextFactory
from ebl.fragment.transliteration import Transliteration
from ebl.text.labels import LineNumberLabel
from ebl.text.line import TextLine
from ebl.text.token import Word

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


def expect_validate_references(bibliography, when, text=TEXT):
    (pydash
     .chain(text.chapters)
     .flat_map(lambda chapter: chapter.manuscripts)
     .map(lambda manuscript: manuscript.references)
     .for_each(lambda references:
               when(bibliography).validate_references(references).thenReturn())
     .value())


def allow_validate_references(bibliography, when):
    when(bibliography).validate_references(...).thenReturn()


def expect_invalid_references(bibliography, when):
    when(bibliography).validate_references(...).thenRaise(DataError())


def expect_signs(sign_list, when, sign='X'):
    (pydash
     .chain(TEXT.chapters)
     .flat_map(lambda chapter: chapter.lines)
     .flat_map(lambda line: line.manuscripts)
     .map(lambda manuscript: manuscript.line.atf)
     .map(lambda atf: Transliteration(atf).cleaned)
     .for_each(lambda cleaned: when(sign_list)
               .map_transliteration(cleaned)
               .thenReturn([[sign]]))
     .value())


def expect_invalid_signs(sign_list, when):
    when(sign_list).map_transliteration(...).thenReturn([['?']])


def test_creating_text(corpus,
                       text_repository,
                       bibliography,
                       changelog,
                       sign_list,
                       user,
                       when):
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


def test_create_raises_exception_if_invalid_signs(corpus,
                                                  bibliography,
                                                  sign_list,
                                                  when):
    allow_validate_references(bibliography, when)
    expect_invalid_signs(sign_list, when)

    with pytest.raises(DataError):
        corpus.create(TEXT, ANY_USER)


def test_create_raises_exception_if_invalid_references(corpus,
                                                       bibliography,
                                                       when):
    expect_invalid_references(bibliography, when)

    with pytest.raises(DataError):
        corpus.create(TEXT, ANY_USER)


def test_finding_text(corpus, text_repository, bibliography, when):
    when(text_repository).find(TEXT.id).thenReturn(DEHYDRATED_TEXT)
    expect_bibliography(bibliography, when)

    assert corpus.find(TEXT.id) == TEXT


def test_listing_texts(corpus, text_repository, when):
    when(text_repository).list().thenReturn([DEHYDRATED_TEXT])

    assert corpus.list() == [DEHYDRATED_TEXT]


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


def test_update_raises_exception_if_invalid_signs(corpus,
                                                  text_repository,
                                                  bibliography,
                                                  sign_list,
                                                  when):
    updated_text = attr.evolve(TEXT, index=TEXT.index + 1, name='New Name')
    when(text_repository).find(TEXT.id).thenReturn(DEHYDRATED_TEXT)
    allow_validate_references(bibliography, when)
    expect_invalid_signs(sign_list, when)

    with pytest.raises(DataError):
        corpus.update(TEXT.id, updated_text, ANY_USER)


def test_update_raises_exception_if_invalid_references(corpus,
                                                       text_repository,
                                                       bibliography,
                                                       when):
    updated_text = attr.evolve(TEXT, index=TEXT.index + 1, name='New Name')
    when(text_repository).find(TEXT.id).thenReturn(DEHYDRATED_TEXT)
    expect_invalid_references(bibliography, when)

    with pytest.raises(DataError):
        corpus.update(TEXT.id, updated_text, ANY_USER)


def test_updating_alignment(corpus,
                            text_repository,
                            bibliography,
                            changelog,
                            sign_list,
                            user,
                            when):
    dehydrated_updated_text = attr.evolve(DEHYDRATED_TEXT, chapters=(
        attr.evolve(DEHYDRATED_TEXT.chapters[0], lines=(
            attr.evolve(DEHYDRATED_TEXT.chapters[0].lines[0], manuscripts=(
                attr.evolve(
                    DEHYDRATED_TEXT.chapters[0].lines[0].manuscripts[0],
                    line=TextLine('1.', (Word('ku]-nu-ši', alignment=0),))
                ),
            )),
        )),
    ))
    expect_signs(sign_list, when)
    expect_validate_references(bibliography, when, DEHYDRATED_TEXT)
    when(text_repository).find(TEXT.id).thenReturn(DEHYDRATED_TEXT)
    (when(text_repository)
     .update(TEXT.id, dehydrated_updated_text)
     .thenReturn(dehydrated_updated_text))
    when(changelog).create(
        COLLECTION,
        user.profile,
        {**to_dict(DEHYDRATED_TEXT), '_id': DEHYDRATED_TEXT.id},
        {**to_dict(dehydrated_updated_text), '_id': dehydrated_updated_text.id}
    ).thenReturn()

    alignment = Alignment((
        (
            (AlignmentToken('ku]-nu-ši', 0),),
        ),
    ))
    corpus.update_alignment(TEXT.id, 0, alignment, user)


@pytest.mark.parametrize('alignment', [
    Alignment((
            (
                    (AlignmentToken('ku]-nu-ši', 0),
                     AlignmentToken('ku]-nu-ši', 0),),
            ),
    )),
    Alignment((
            (
                    tuple(),
            ),
    )),
    Alignment((
            (
                    (AlignmentToken('ku]-nu-ši', 0),),
                    (AlignmentToken('ku]-nu-ši', 0),)
            ),
    )),
    Alignment((
            tuple()
    )),
    Alignment((
            (
                    (AlignmentToken('ku]-nu-ši', 0),),
            ),
            (
                    (AlignmentToken('ku]-nu-ši', 0),),
            )
    )),
    Alignment(tuple()),
    Alignment((
        (
            (AlignmentToken('invalid value', 0),),
        ),
    ))

])
def test_invalid_alignment(alignment,
                           corpus,
                           text_repository,
                           when):
    when(text_repository).find(TEXT.id).thenReturn(DEHYDRATED_TEXT)
    with pytest.raises(AlignmentError):
        corpus.update_alignment(TEXT.id, 0, alignment, ANY_USER)


def test_updating_manuscripts(corpus,
                              text_repository,
                              bibliography,
                              changelog,
                              sign_list,
                              user,
                              when):
    dehydrated_updated_text = attr.evolve(DEHYDRATED_TEXT, chapters=(
        attr.evolve(DEHYDRATED_TEXT.chapters[0], manuscripts=(
            attr.evolve(DEHYDRATED_TEXT.chapters[0].manuscripts[0],
                        notes='Updated manuscript.'),
        )),
    ))
    expect_signs(sign_list, when)
    expect_validate_references(bibliography, when, DEHYDRATED_TEXT)
    when(text_repository).find(TEXT.id).thenReturn(DEHYDRATED_TEXT)
    (when(text_repository)
     .update(TEXT.id, dehydrated_updated_text)
     .thenReturn(dehydrated_updated_text))
    when(changelog).create(
        COLLECTION,
        user.profile,
        {**to_dict(DEHYDRATED_TEXT), '_id': DEHYDRATED_TEXT.id},
        {**to_dict(dehydrated_updated_text), '_id': dehydrated_updated_text.id}
    ).thenReturn()

    manuscripts = (
        dehydrated_updated_text.chapters[0].manuscripts[0],
    )
    corpus.update_manuscripts(TEXT.id, 0, manuscripts, user)


@pytest.mark.parametrize('manuscripts', [
    tuple(),
    (
        DEHYDRATED_TEXT.chapters[0].manuscripts[0],
        DEHYDRATED_TEXT.chapters[0].manuscripts[0]
    )
])
def test_invalid_manuscripts(manuscripts,
                             corpus,
                             text_repository,
                             when):
    when(text_repository).find(TEXT.id).thenReturn(DEHYDRATED_TEXT)
    with pytest.raises(DataError):
        corpus.update_manuscripts(TEXT.id, 0, manuscripts, ANY_USER)


def test_updating_lines(corpus,
                        text_repository,
                        bibliography,
                        changelog,
                        sign_list,
                        user,
                        when):
    dehydrated_updated_text = attr.evolve(DEHYDRATED_TEXT, chapters=(
        attr.evolve(DEHYDRATED_TEXT.chapters[0], lines=(
            attr.evolve(DEHYDRATED_TEXT.chapters[0].lines[0],
                        number=LineNumberLabel.from_atf("1'.")),
        )),
    ))
    expect_signs(sign_list, when)
    expect_validate_references(bibliography, when, DEHYDRATED_TEXT)
    when(text_repository).find(TEXT.id).thenReturn(DEHYDRATED_TEXT)
    (when(text_repository)
     .update(TEXT.id, dehydrated_updated_text)
     .thenReturn(dehydrated_updated_text))
    when(changelog).create(
        COLLECTION,
        user.profile,
        {**to_dict(DEHYDRATED_TEXT), '_id': DEHYDRATED_TEXT.id},
        {**to_dict(dehydrated_updated_text), '_id': dehydrated_updated_text.id}
    ).thenReturn()

    lines = dehydrated_updated_text.chapters[0].lines
    corpus.update_lines(TEXT.id, 0, lines, user)
