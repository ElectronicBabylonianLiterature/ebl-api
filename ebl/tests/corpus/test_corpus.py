import attr
import pytest  # pyre-ignore[21]

from ebl.corpus.application.lemmatization import (
    ChapterLemmatization,
    LineVariantLemmatization,
)
from ebl.corpus.application.text_serializer import serialize
from ebl.corpus.domain.alignment import Alignment, ManuscriptLineAlignment
from ebl.corpus.domain.chapter import Line, LineVariant, ManuscriptLine
from ebl.dictionary.domain.word import WordId
from ebl.errors import DataError, Defect, NotFoundError
from ebl.tests.factories.corpus import TextFactory
from ebl.transliteration.domain.alignment import AlignmentError, AlignmentToken
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.lemmatization import LemmatizationToken
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Joiner, ValueToken
from ebl.transliteration.domain.word_tokens import Word
from ebl.users.domain.user import Guest

COLLECTION = "texts"
TEXT = TextFactory.build()  # pyre-ignore[16]
TEXT_WITHOUT_DOCUMENTS = attr.evolve(
    TEXT,
    chapters=tuple(
        attr.evolve(
            chapter,
            manuscripts=tuple(
                attr.evolve(
                    manuscript,
                    references=tuple(
                        attr.evolve(reference, document=None)
                        for reference in manuscript.references
                    ),
                )
                for manuscript in chapter.manuscripts
            ),
        )
        for chapter in TEXT.chapters
    ),
)
ANY_USER = Guest()


def expect_bibliography(bibliography, when) -> None:
    for chapter in TEXT.chapters:
        for manuscript in chapter.manuscripts:
            for reference in manuscript.references:
                (when(bibliography).find(reference.id).thenReturn(reference.document))


def expect_validate_references(bibliography, when, text=TEXT) -> None:
    manuscript_references = [
        manuscript.references
        for chapter in text.chapters
        for manuscript in chapter.manuscripts
    ]

    for references in manuscript_references:
        when(bibliography).validate_references(references).thenReturn()


def allow_validate_references(bibliography, when) -> None:
    when(bibliography).validate_references(...).thenReturn()


def expect_invalid_references(bibliography, when) -> None:
    when(bibliography).validate_references(...).thenRaise(DataError())


def expect_signs(signs, sign_repository) -> None:
    for sign in signs:
        sign_repository.create(sign)


def expect_text_update(
    bibliography,
    changelog,
    old_text,
    updated_text,
    signs,
    sign_repository,
    text_repository,
    user,
    when,
) -> None:
    expect_signs(signs, sign_repository)
    expect_validate_references(bibliography, when, old_text)
    when(text_repository).update(TEXT.id, updated_text).thenReturn(updated_text)
    when(changelog).create(
        COLLECTION,
        user.profile,
        {**serialize(old_text), "_id": (old_text.id.category, old_text.id.index)},
        {
            **serialize(updated_text),
            "_id": (updated_text.id.category, updated_text.id.index),
        },
    ).thenReturn()


def expect_text_find_and_update(
    bibliography,
    changelog,
    old_text,
    updated_text,
    signs,
    sign_repository,
    text_repository,
    user,
    when,
) -> None:
    when(text_repository).find(TEXT.id).thenReturn(old_text)
    expect_text_update(
        bibliography,
        changelog,
        old_text,
        updated_text,
        signs,
        sign_repository,
        text_repository,
        user,
        when,
    )


def test_creating_text(
    corpus, text_repository, bibliography, changelog, signs, sign_repository, user, when
) -> None:
    expect_signs(signs, sign_repository)
    expect_validate_references(bibliography, when)
    text_id = (TEXT.id.category, TEXT.id.index)
    when(changelog).create(
        COLLECTION, user.profile, {"_id": text_id}, {**serialize(TEXT), "_id": text_id}
    ).thenReturn()
    when(text_repository).create(TEXT).thenReturn()

    corpus.create(TEXT, user)


def test_create_raises_exception_if_invalid_signs(corpus, bibliography, when) -> None:
    allow_validate_references(bibliography, when)

    with pytest.raises(DataError):
        corpus.create(TEXT, ANY_USER)


def test_create_raises_exception_if_invalid_references(
    corpus, bibliography, when
) -> None:
    expect_invalid_references(bibliography, when)

    with pytest.raises(DataError):
        corpus.create(TEXT, ANY_USER)


def test_finding_text(corpus, text_repository, bibliography, when) -> None:
    when(text_repository).find(TEXT.id).thenReturn(TEXT_WITHOUT_DOCUMENTS)
    expect_bibliography(bibliography, when)

    assert corpus.find(TEXT.id) == TEXT


def test_listing_texts(corpus, text_repository, when) -> None:
    when(text_repository).list().thenReturn([TEXT_WITHOUT_DOCUMENTS])

    assert corpus.list() == [TEXT_WITHOUT_DOCUMENTS]


def test_find_raises_exception_if_references_not_found(
    corpus, text_repository, bibliography, when
) -> None:
    when(text_repository).find(TEXT.id).thenReturn(TEXT_WITHOUT_DOCUMENTS)
    when(bibliography).find(...).thenRaise(NotFoundError())

    with pytest.raises(Defect):
        corpus.find(TEXT.id)


def test_updating_text(
    corpus, text_repository, bibliography, changelog, signs, sign_repository, user, when
) -> None:
    updated_text = attr.evolve(TEXT_WITHOUT_DOCUMENTS, name="New Name")
    expect_text_update(
        bibliography,
        changelog,
        TEXT_WITHOUT_DOCUMENTS,
        updated_text,
        signs,
        sign_repository,
        text_repository,
        user,
        when,
    )

    corpus.update_text(
        TEXT_WITHOUT_DOCUMENTS.id, TEXT_WITHOUT_DOCUMENTS, updated_text, user
    )


def test_updating_alignment(
    corpus, text_repository, bibliography, changelog, signs, sign_repository, user, when
) -> None:
    aligmnet = 0
    omitted_words = (1,)
    updated_text = attr.evolve(
        TEXT_WITHOUT_DOCUMENTS,
        chapters=(
            attr.evolve(
                TEXT_WITHOUT_DOCUMENTS.chapters[0],
                lines=(
                    attr.evolve(
                        TEXT_WITHOUT_DOCUMENTS.chapters[0].lines[0],
                        variants=(
                            attr.evolve(
                                TEXT_WITHOUT_DOCUMENTS.chapters[0].lines[0].variants[0],
                                manuscripts=(
                                    attr.evolve(
                                        TEXT_WITHOUT_DOCUMENTS.chapters[0]
                                        .lines[0]
                                        .variants[0]
                                        .manuscripts[0],
                                        line=TextLine.of_iterable(
                                            TEXT_WITHOUT_DOCUMENTS.chapters[0]
                                            .lines[0]
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
                                                    alignment=aligmnet,
                                                ),
                                            ),
                                        ),
                                        omitted_words=omitted_words,
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )
    expect_text_find_and_update(
        bibliography,
        changelog,
        TEXT_WITHOUT_DOCUMENTS,
        updated_text,
        signs,
        sign_repository,
        text_repository,
        user,
        when,
    )

    alignment = Alignment(
        (
            (
                (
                    ManuscriptLineAlignment(
                        (AlignmentToken("ku-[nu-ši]", aligmnet),), omitted_words
                    ),
                ),
            ),
        )
    )
    corpus.update_alignment(TEXT.id, 0, alignment, user)


def test_updating_manuscript_lemmatization(
    corpus, text_repository, bibliography, changelog, signs, sign_repository, user, when
) -> None:
    updated_text = attr.evolve(
        TEXT_WITHOUT_DOCUMENTS,
        chapters=(
            attr.evolve(
                TEXT_WITHOUT_DOCUMENTS.chapters[0],
                lines=(
                    attr.evolve(
                        TEXT_WITHOUT_DOCUMENTS.chapters[0].lines[0],
                        variants=(
                            attr.evolve(
                                TEXT_WITHOUT_DOCUMENTS.chapters[0].lines[0].variants[0],
                                reconstruction=(
                                    TEXT_WITHOUT_DOCUMENTS.chapters[0]
                                    .lines[0]
                                    .variants[0]
                                    .reconstruction[0],
                                    TEXT_WITHOUT_DOCUMENTS.chapters[0]
                                    .lines[0]
                                    .variants[0]
                                    .reconstruction[1]
                                    .set_unique_lemma(
                                        LemmatizationToken(
                                            TEXT_WITHOUT_DOCUMENTS.chapters[0]
                                            .lines[0]
                                            .variants[0]
                                            .reconstruction[1]
                                            .value,
                                            (WordId("aklu I"),),
                                        )
                                    ),
                                    *TEXT_WITHOUT_DOCUMENTS.chapters[0]
                                    .lines[0]
                                    .variants[0]
                                    .reconstruction[2:6],
                                    TEXT_WITHOUT_DOCUMENTS.chapters[0]
                                    .lines[0]
                                    .variants[0]
                                    .reconstruction[6]
                                    .set_unique_lemma(
                                        LemmatizationToken(
                                            TEXT_WITHOUT_DOCUMENTS.chapters[0]
                                            .lines[0]
                                            .variants[0]
                                            .reconstruction[6]
                                            .value,
                                            tuple(),
                                        )
                                    ),
                                ),
                                manuscripts=(
                                    attr.evolve(
                                        TEXT_WITHOUT_DOCUMENTS.chapters[0]
                                        .lines[0]
                                        .variants[0]
                                        .manuscripts[0],
                                        line=TextLine.of_iterable(
                                            TEXT_WITHOUT_DOCUMENTS.chapters[0]
                                            .lines[0]
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
                                                    unique_lemma=(WordId("aklu I"),),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )
    expect_text_find_and_update(
        bibliography,
        changelog,
        TEXT_WITHOUT_DOCUMENTS,
        updated_text,
        signs,
        sign_repository,
        text_repository,
        user,
        when,
    )

    lemmatization: ChapterLemmatization = (
        (
            LineVariantLemmatization(
                (
                    LemmatizationToken("%n"),
                    LemmatizationToken("buāru", (WordId("aklu I"),)),
                    LemmatizationToken("(|)"),
                    LemmatizationToken("["),
                    LemmatizationToken("..."),
                    LemmatizationToken("||"),
                    LemmatizationToken("...]-buāru#", tuple()),
                ),
                ((LemmatizationToken("ku-[nu-ši]", (WordId("aklu I"),)),),),
            ),
        ),
    )
    corpus.update_manuscript_lemmatization(TEXT.id, 0, lemmatization, user)


@pytest.mark.parametrize(  # pyre-ignore[56]
    "alignment",
    [
        Alignment(
            (
                (
                    (
                        ManuscriptLineAlignment(
                            (
                                AlignmentToken("ku-[nu-ši]", 0),
                                AlignmentToken("ku-[nu-ši]", 0),
                            )
                        ),
                    ),
                ),
            )
        ),
        Alignment(
            (
                (
                    (
                        ManuscriptLineAlignment((AlignmentToken("ku-[nu-ši]", 0),)),
                        ManuscriptLineAlignment((AlignmentToken("ku-[nu-ši]", 0),)),
                    ),
                ),
            )
        ),
        Alignment(
            (
                ((ManuscriptLineAlignment((AlignmentToken("ku-[nu-ši]", 0),)),),),
                ((ManuscriptLineAlignment((AlignmentToken("ku-[nu-ši]", 0),)),),),
            )
        ),
        Alignment((((ManuscriptLineAlignment(tuple()),),),)),
        Alignment(((tuple(),),)),
        Alignment((tuple(),)),
        Alignment(tuple()),
        Alignment(
            (((ManuscriptLineAlignment((AlignmentToken("invalid value", 0),)),),),)
        ),
    ],
)
def test_invalid_alignment(alignment, corpus, text_repository, when) -> None:
    when(text_repository).find(TEXT.id).thenReturn(TEXT_WITHOUT_DOCUMENTS)
    with pytest.raises(AlignmentError):
        corpus.update_alignment(TEXT.id, 0, alignment, ANY_USER)


def test_updating_manuscripts(
    corpus, text_repository, bibliography, changelog, signs, sign_repository, user, when
) -> None:
    updated_text = attr.evolve(
        TEXT_WITHOUT_DOCUMENTS,
        chapters=(
            attr.evolve(
                TEXT_WITHOUT_DOCUMENTS.chapters[0],
                manuscripts=(
                    attr.evolve(
                        TEXT_WITHOUT_DOCUMENTS.chapters[0].manuscripts[0],
                        notes="Updated manuscript.",
                    ),
                ),
            ),
        ),
    )
    expect_text_find_and_update(
        bibliography,
        changelog,
        TEXT_WITHOUT_DOCUMENTS,
        updated_text,
        signs,
        sign_repository,
        text_repository,
        user,
        when,
    )

    manuscripts = (updated_text.chapters[0].manuscripts[0],)
    corpus.update_manuscripts(TEXT.id, 0, manuscripts, user)


@pytest.mark.parametrize(  # pyre-ignore[56]
    "manuscripts",
    [
        tuple(),
        (
            TEXT_WITHOUT_DOCUMENTS.chapters[0].manuscripts[0],
            TEXT_WITHOUT_DOCUMENTS.chapters[0].manuscripts[0],
        ),
    ],
)
def test_invalid_manuscripts(manuscripts, corpus, text_repository, when) -> None:
    when(text_repository).find(TEXT.id).thenReturn(TEXT_WITHOUT_DOCUMENTS)
    with pytest.raises(DataError):
        corpus.update_manuscripts(TEXT.id, 0, manuscripts, ANY_USER)


def test_update_manuscripts_raises_exception_if_invalid_references(
    corpus, text_repository, bibliography, when
) -> None:
    manuscripts = TEXT.chapters[0].manuscripts
    when(text_repository).find(TEXT.id).thenReturn(TEXT_WITHOUT_DOCUMENTS)
    expect_invalid_references(bibliography, when)

    with pytest.raises(DataError):
        corpus.update_manuscripts(TEXT.id, 0, manuscripts, ANY_USER)


def test_updating_lines(
    corpus, text_repository, bibliography, changelog, signs, sign_repository, user, when
) -> None:
    updated_text = attr.evolve(
        TEXT_WITHOUT_DOCUMENTS,
        chapters=(
            attr.evolve(
                TEXT_WITHOUT_DOCUMENTS.chapters[0],
                lines=(
                    attr.evolve(
                        TEXT_WITHOUT_DOCUMENTS.chapters[0].lines[0],
                        number=LineNumber(1, True),
                    ),
                ),
                parser_version=ATF_PARSER_VERSION,
            ),
        ),
    )
    expect_text_find_and_update(
        bibliography,
        changelog,
        TEXT_WITHOUT_DOCUMENTS,
        updated_text,
        signs,
        sign_repository,
        text_repository,
        user,
        when,
    )

    lines = updated_text.chapters[0].lines
    corpus.update_lines(TEXT.id, 0, lines, user)


def test_merging_lines(
    corpus, text_repository, bibliography, changelog, signs, sign_repository, user, when
) -> None:
    reconstruction = (AkkadianWord.of((ValueToken.of("buāru"),)),)
    is_second_line_of_parallelism = False
    is_beginning_of_section = False
    text_line = TextLine.of_iterable(
        LineNumber(1),
        (
            Word.of(
                [Reading.of_name("ku")], unique_lemma=(WordId("word1"),), alignment=0
            ),
            Word.of(
                [Reading.of_name("nu")], unique_lemma=(WordId("word2"),), alignment=1
            ),
        ),
    )
    manuscript_id = TEXT_WITHOUT_DOCUMENTS.chapters[0].manuscripts[0].id
    line = Line(
        LineNumber(1),
        (
            LineVariant(
                reconstruction,
                None,
                (ManuscriptLine(manuscript_id, tuple(), text_line),),
            ),
        ),
        not is_second_line_of_parallelism,
        not is_beginning_of_section,
    )
    new_text_line = TextLine.of_iterable(
        LineNumber(1),
        (Word.of([Reading.of_name("ku")]), Word.of([Reading.of_name("ši")])),
    )
    new_line = Line(
        LineNumber(1),
        (
            LineVariant(
                reconstruction,
                None,
                (
                    ManuscriptLine(
                        manuscript_id, tuple(), text_line.merge(new_text_line)
                    ),
                ),
            ),
        ),
        is_second_line_of_parallelism,
        is_beginning_of_section,
    )
    dehydrated_text = attr.evolve(
        TEXT_WITHOUT_DOCUMENTS,
        chapters=(attr.evolve(TEXT_WITHOUT_DOCUMENTS.chapters[0], lines=(line,)),),
    )
    updated_text = attr.evolve(
        TEXT_WITHOUT_DOCUMENTS,
        chapters=(
            attr.evolve(
                TEXT_WITHOUT_DOCUMENTS.chapters[0],
                lines=(new_line,),
                parser_version=ATF_PARSER_VERSION,
            ),
        ),
    )
    expect_text_find_and_update(
        bibliography,
        changelog,
        dehydrated_text,
        updated_text,
        signs,
        sign_repository,
        text_repository,
        user,
        when,
    )

    lines = (
        Line(
            LineNumber(1),
            (
                LineVariant(
                    reconstruction,
                    None,
                    (ManuscriptLine(manuscript_id, tuple(), new_text_line),),
                ),
            ),
            is_second_line_of_parallelism,
            is_beginning_of_section,
        ),
    )
    corpus.update_lines(TEXT.id, 0, lines, user)


def test_update_lines_raises_exception_if_invalid_signs(
    corpus, text_repository, bibliography, when
) -> None:
    lines = TEXT.chapters[0].lines
    when(text_repository).find(TEXT.id).thenReturn(TEXT_WITHOUT_DOCUMENTS)
    allow_validate_references(bibliography, when)

    with pytest.raises(DataError):
        corpus.update_lines(TEXT.id, 0, lines, ANY_USER)
