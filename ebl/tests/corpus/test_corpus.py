import attr
import pytest

from ebl.corpus.application.lemmatization import (
    ChapterLemmatization,
    LineVariantLemmatization,
)
from ebl.corpus.application.schemas import ChapterSchema
from ebl.corpus.domain.alignment import Alignment, ManuscriptLineAlignment
from ebl.corpus.domain.chapter_display import ChapterDisplay
from ebl.corpus.domain.line import Line, LineVariant, ManuscriptLine
from ebl.corpus.domain.lines_update import LinesUpdate
from ebl.corpus.domain.parser import parse_chapter
from ebl.dictionary.domain.word import WordId
from ebl.errors import DataError, Defect, NotFoundError
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.lemmatization.domain.lemmatization import LemmatizationToken
from ebl.tests.corpus.support import ANY_USER
from ebl.tests.factories.corpus import ChapterFactory, TextFactory
from ebl.transliteration.domain.alignment import AlignmentError, AlignmentToken
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text import Text as Transliteration
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Joiner, LanguageShift, ValueToken
from ebl.transliteration.domain.word_tokens import Word


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


def expect_bibliography(bibliography, when) -> None:
    for manuscript in CHAPTER.manuscripts:
        for reference in manuscript.references:
            (when(bibliography).find(reference.id).thenReturn(reference.document))


def expect_invalid_references(bibliography, when) -> None:
    when(bibliography).find(...).thenRaise(NotFoundError())


def expect_signs(signs, sign_repository) -> None:
    for sign in signs:
        sign_repository.create(sign)


def expect_chapter_update(
    bibliography,
    changelog,
    old_chapter,
    updated_chapter,
    signs,
    sign_repository,
    text_repository,
    user,
    when,
) -> None:
    expect_signs(signs, sign_repository)
    when(text_repository).update(CHAPTER.id_, updated_chapter).thenReturn(
        updated_chapter
    )
    when(changelog).create(
        CHAPTERS_COLLECTION,
        user.profile,
        {**ChapterSchema().dump(old_chapter), "_id": old_chapter.id_.to_tuple()},
        {
            **ChapterSchema().dump(updated_chapter),
            "_id": updated_chapter.id_.to_tuple(),
        },
    ).thenReturn()


def expect_find_and_update_chapter(
    bibliography,
    changelog,
    old_chapter,
    updated_chapter,
    signs,
    sign_repository,
    text_repository,
    user,
    when,
) -> None:
    when(text_repository).find_chapter(CHAPTER.id_).thenReturn(old_chapter)
    expect_bibliography(bibliography, when)
    expect_chapter_update(
        bibliography,
        changelog,
        old_chapter,
        updated_chapter,
        signs,
        sign_repository,
        text_repository,
        user,
        when,
    )


def test_find_text(corpus, text_repository, bibliography, when) -> None:
    when(text_repository).find(TEXT.id).thenReturn(TEXT)

    assert corpus.find(TEXT.id) == TEXT


def test_listing_texts(corpus, text_repository, when) -> None:
    when(text_repository).list().thenReturn([TEXT])

    assert corpus.list() == [TEXT]


def test_find_chapter(corpus, text_repository, bibliography, when) -> None:
    when(text_repository).find_chapter(CHAPTER.id_).thenReturn(
        CHAPTER_WITHOUT_DOCUMENTS
    )
    expect_bibliography(bibliography, when)

    assert corpus.find_chapter(CHAPTER.id_) == CHAPTER


def test_find_chapter_for_display(
    corpus, text_repository, parallel_line_injector, when
) -> None:
    chapter_display = ChapterDisplay.of_chapter(TEXT, CHAPTER)
    injected_chapter_display = attr.evolve(
        chapter_display,
        lines=tuple(
            attr.evolve(
                line,
                parallel_lines=parallel_line_injector.inject(line.parallel_lines),
            )
            for line in chapter_display.lines
        ),
    )
    when(text_repository).find_chapter_for_display(CHAPTER.id_).thenReturn(
        chapter_display
    )

    assert corpus.find_chapter_for_display(CHAPTER.id_) == injected_chapter_display


def test_find_line(corpus, text_repository, bibliography, when) -> None:
    number = 0
    when(text_repository).find_line(CHAPTER.id_, number).thenReturn(
        CHAPTER_WITHOUT_DOCUMENTS.lines[number]
    )
    when(text_repository).query_manuscripts_by_chapter(CHAPTER.id_).thenReturn(
        CHAPTER.manuscripts
    )
    expect_bibliography(bibliography, when)

    assert corpus.find_line(CHAPTER.id_, number) == (
        CHAPTER.lines[number],
        CHAPTER.manuscripts,
    )


def test_find_manuscripts(corpus, text_repository, bibliography, when) -> None:
    expect_bibliography(bibliography, when)
    when(text_repository).query_manuscripts_by_chapter(CHAPTER.id_).thenReturn(
        CHAPTER.manuscripts
    )

    assert corpus.find_manuscripts(CHAPTER.id_) == CHAPTER.manuscripts


def test_find_manuscripts_with_joins(
    corpus, text_repository, bibliography, when
) -> None:
    expect_bibliography(bibliography, when)
    when(text_repository).query_manuscripts_with_joins_by_chapter(
        CHAPTER.id_
    ).thenReturn(CHAPTER.manuscripts)

    assert corpus.find_manuscripts_with_joins(CHAPTER.id_) == CHAPTER.manuscripts


def test_find_chapter_raises_exception_if_references_not_found(
    corpus, text_repository, bibliography, when
) -> None:
    when(text_repository).find_chapter(CHAPTER.id_).thenReturn(
        CHAPTER_WITHOUT_DOCUMENTS
    )
    when(bibliography).find(...).thenRaise(NotFoundError())

    with pytest.raises(Defect):
        corpus.find_chapter(CHAPTER.id_)


def test_update_chapter(
    corpus, text_repository, bibliography, changelog, signs, sign_repository, user, when
) -> None:
    updated_chapter = attr.evolve(CHAPTER, version="New Version")
    expect_chapter_update(
        bibliography,
        changelog,
        CHAPTER_WITHOUT_DOCUMENTS,
        updated_chapter,
        signs,
        sign_repository,
        text_repository,
        user,
        when,
    )

    corpus.update_chapter(
        CHAPTER_WITHOUT_DOCUMENTS.id_, CHAPTER_WITHOUT_DOCUMENTS, updated_chapter, user
    )


def test_updating_alignment(
    corpus, text_repository, bibliography, changelog, signs, sign_repository, user, when
) -> None:
    aligmnet = 0
    omitted_words = (1,)
    updated_chapter = attr.evolve(
        CHAPTER,
        lines=(
            attr.evolve(
                CHAPTER.lines[0],
                variants=(
                    attr.evolve(
                        CHAPTER.lines[0].variants[0],
                        manuscripts=(
                            attr.evolve(
                                CHAPTER.lines[0].variants[0].manuscripts[0],
                                line=TextLine.of_iterable(
                                    CHAPTER.lines[0]
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
    )
    expect_find_and_update_chapter(
        bibliography,
        changelog,
        CHAPTER_WITHOUT_DOCUMENTS,
        updated_chapter,
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
    assert corpus.update_alignment(CHAPTER.id_, alignment, user) == updated_chapter


def test_updating_manuscript_lemmatization(
    corpus, text_repository, bibliography, changelog, signs, sign_repository, user, when
) -> None:
    updated_chapter = attr.evolve(
        CHAPTER,
        lines=(
            attr.evolve(
                CHAPTER.lines[0],
                variants=(
                    attr.evolve(
                        CHAPTER.lines[0].variants[0],
                        reconstruction=(
                            CHAPTER.lines[0].variants[0].reconstruction[0],
                            CHAPTER.lines[0]
                            .variants[0]
                            .reconstruction[1]
                            .set_unique_lemma(
                                LemmatizationToken(
                                    CHAPTER_WITHOUT_DOCUMENTS.lines[0]
                                    .variants[0]
                                    .reconstruction[1]
                                    .value,
                                    (WordId("aklu I"),),
                                )
                            ),
                            *CHAPTER.lines[0].variants[0].reconstruction[2:6],
                            CHAPTER.lines[0]
                            .variants[0]
                            .reconstruction[6]
                            .set_unique_lemma(
                                LemmatizationToken(
                                    CHAPTER.lines[0]
                                    .variants[0]
                                    .reconstruction[6]
                                    .value,
                                    tuple(),
                                )
                            ),
                        ),
                        manuscripts=(
                            attr.evolve(
                                CHAPTER.lines[0].variants[0].manuscripts[0],
                                line=TextLine.of_iterable(
                                    CHAPTER.lines[0]
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
    )
    expect_find_and_update_chapter(
        bibliography,
        changelog,
        CHAPTER_WITHOUT_DOCUMENTS,
        updated_chapter,
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
    assert (
        corpus.update_manuscript_lemmatization(CHAPTER.id_, lemmatization, user)
        == updated_chapter
    )


@pytest.mark.parametrize(
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
def test_invalid_alignment(
    alignment, corpus, text_repository, bibliography, when
) -> None:
    when(text_repository).find_chapter(CHAPTER.id_).thenReturn(
        CHAPTER_WITHOUT_DOCUMENTS
    )
    expect_bibliography(bibliography, when)
    with pytest.raises(AlignmentError):
        corpus.update_alignment(CHAPTER.id_, alignment, ANY_USER)


def test_updating_manuscripts(
    corpus, text_repository, bibliography, changelog, signs, sign_repository, user, when
) -> None:
    uncertain_fragments = (MuseumNumber.of("K.1"),)
    updated_chapter = attr.evolve(
        CHAPTER,
        manuscripts=(
            attr.evolve(
                CHAPTER.manuscripts[0],
                colophon=Transliteration.of_iterable(
                    [
                        TextLine.of_iterable(
                            LineNumber(1, True), (Word.of([Reading.of_name("ba")]),)
                        )
                    ]
                ),
                unplaced_lines=Transliteration.of_iterable(
                    [
                        TextLine.of_iterable(
                            LineNumber(1, True), (Word.of([Reading.of_name("ku")]),)
                        )
                    ]
                ),
                notes="Updated manuscript.",
            ),
        ),
        uncertain_fragments=uncertain_fragments,
        signs=("KU ABZ075 ABZ207a\\u002F207b\\u0020X\nBA\nKU",),
    )
    expect_find_and_update_chapter(
        bibliography,
        changelog,
        CHAPTER_WITHOUT_DOCUMENTS,
        updated_chapter,
        signs,
        sign_repository,
        text_repository,
        user,
        when,
    )

    manuscripts = (updated_chapter.manuscripts[0],)
    assert (
        corpus.update_manuscripts(CHAPTER.id_, manuscripts, uncertain_fragments, user)
        == updated_chapter
    )


@pytest.mark.parametrize(
    "manuscripts",
    [
        tuple(),
        (
            CHAPTER_WITHOUT_DOCUMENTS.manuscripts[0],
            CHAPTER_WITHOUT_DOCUMENTS.manuscripts[0],
        ),
    ],
)
def test_invalid_manuscripts(
    manuscripts, corpus, text_repository, bibliography, when
) -> None:
    when(text_repository).find_chapter(CHAPTER.id_).thenReturn(
        CHAPTER_WITHOUT_DOCUMENTS
    )
    expect_bibliography(bibliography, when)
    with pytest.raises(DataError):
        corpus.update_manuscripts(CHAPTER.id_, manuscripts, tuple(), ANY_USER)


def test_update_manuscripts_raises_exception_if_invalid_references(
    corpus, text_repository, bibliography, when
) -> None:
    manuscripts = CHAPTER.manuscripts
    expect_invalid_references(bibliography, when)

    with pytest.raises(DataError):
        corpus.update_manuscripts(CHAPTER.id_, manuscripts, tuple(), ANY_USER)


def test_updating_lines_edit(
    corpus, text_repository, bibliography, changelog, signs, sign_repository, user, when
) -> None:
    updated_chapter = attr.evolve(
        CHAPTER,
        lines=(
            attr.evolve(
                CHAPTER.lines[0],
                number=LineNumber(1, True),
                variants=(
                    attr.evolve(
                        CHAPTER.lines[0].variants[0],
                        manuscripts=(
                            attr.evolve(
                                CHAPTER.lines[0].variants[0].manuscripts[0],
                                line=TextLine.of_iterable(
                                    LineNumber(1, True),
                                    (
                                        Word.of(
                                            [
                                                Reading.of_name("nu"),
                                                Joiner.hyphen(),
                                                BrokenAway.open(),
                                                Reading.of_name("ku"),
                                                Joiner.hyphen(),
                                                Reading.of_name("ši"),
                                                BrokenAway.close(),
                                            ]
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        signs=("ABZ075 KU ABZ207a\\u002F207b\\u0020X\nKU\nABZ075",),
        parser_version=ATF_PARSER_VERSION,
    )
    expect_find_and_update_chapter(
        bibliography,
        changelog,
        CHAPTER_WITHOUT_DOCUMENTS,
        updated_chapter,
        signs,
        sign_repository,
        text_repository,
        user,
        when,
    )

    assert (
        corpus.update_lines(
            CHAPTER.id_, LinesUpdate([], set(), {0: updated_chapter.lines[0]}), user
        )
        == updated_chapter
    )


def test_updating_lines_delete(
    corpus, text_repository, bibliography, changelog, signs, sign_repository, user, when
) -> None:
    updated_chapter = attr.evolve(
        CHAPTER,
        lines=CHAPTER.lines[1:],
        signs=("KU\nABZ075",),
        parser_version=ATF_PARSER_VERSION,
    )
    expect_find_and_update_chapter(
        bibliography,
        changelog,
        CHAPTER_WITHOUT_DOCUMENTS,
        updated_chapter,
        signs,
        sign_repository,
        text_repository,
        user,
        when,
    )

    assert (
        corpus.update_lines(CHAPTER.id_, LinesUpdate([], {0}, {}), user)
        == updated_chapter
    )


def test_updating_lines_add(
    corpus, text_repository, bibliography, changelog, signs, sign_repository, user, when
) -> None:
    updated_chapter = attr.evolve(
        CHAPTER,
        lines=(
            CHAPTER.lines[0],
            attr.evolve(
                CHAPTER.lines[0],
                number=LineNumber(2, True),
                variants=(
                    attr.evolve(
                        CHAPTER.lines[0].variants[0],
                        manuscripts=(
                            attr.evolve(
                                CHAPTER.lines[0].variants[0].manuscripts[0],
                                line=TextLine.of_iterable(
                                    LineNumber(2, True),
                                    (Word.of([Reading.of_name("nu")]),),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        signs=("KU ABZ075 ABZ207a\\u002F207b\\u0020X\nABZ075\nKU\nABZ075",),
        parser_version=ATF_PARSER_VERSION,
    )
    expect_find_and_update_chapter(
        bibliography,
        changelog,
        CHAPTER_WITHOUT_DOCUMENTS,
        updated_chapter,
        signs,
        sign_repository,
        text_repository,
        user,
        when,
    )

    assert (
        corpus.update_lines(
            CHAPTER.id_, LinesUpdate([updated_chapter.lines[1]], set(), {}), user
        )
        == updated_chapter
    )


def test_importing_lines(
    corpus, text_repository, bibliography, changelog, signs, sign_repository, user, when
) -> None:
    line_number = CHAPTER_WITHOUT_DOCUMENTS.lines[-1].number.number + 1
    siglum = CHAPTER_WITHOUT_DOCUMENTS.manuscripts[0].siglum
    atf = f"{line_number}. kur\n{siglum} {line_number}. ba"
    updated_chapter = attr.evolve(
        CHAPTER,
        lines=(  # pyre-ignore[60]
            *CHAPTER.lines,
            *parse_chapter(atf, CHAPTER.manuscripts),
        ),
        signs=("KU ABZ075 ABZ207a\\u002F207b\\u0020X\nBA\nKU\nABZ075",),
        parser_version=ATF_PARSER_VERSION,
    )
    expect_find_and_update_chapter(
        bibliography,
        changelog,
        CHAPTER_WITHOUT_DOCUMENTS,
        updated_chapter,
        signs,
        sign_repository,
        text_repository,
        user,
        when,
    )

    assert corpus.import_lines(CHAPTER.id_, atf, user) == updated_chapter


def test_merging_lines(
    corpus, text_repository, bibliography, changelog, signs, sign_repository, user, when
) -> None:
    reconstruction = (
        LanguageShift.normalized_akkadian(),
        AkkadianWord.of((ValueToken.of("buāru"),)),
    )
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
    manuscript_id = CHAPTER_WITHOUT_DOCUMENTS.manuscripts[0].id
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
        (Word.of([Reading.of_name("ku")]), Word.of([Reading.of_name("ba")])),
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
    old_chapter = attr.evolve(CHAPTER_WITHOUT_DOCUMENTS, lines=(line,))
    updated_chapter = attr.evolve(
        CHAPTER,
        lines=(new_line,),
        signs=("KU BA\nKU\nABZ075",),
        parser_version=ATF_PARSER_VERSION,
    )
    expect_find_and_update_chapter(
        bibliography,
        changelog,
        old_chapter,
        updated_chapter,
        signs,
        sign_repository,
        text_repository,
        user,
        when,
    )

    assert (
        corpus.update_lines(
            CHAPTER.id_,
            LinesUpdate(
                [],
                set(),
                {
                    0: Line(
                        LineNumber(1),
                        (
                            LineVariant(
                                reconstruction,
                                None,
                                (
                                    ManuscriptLine(
                                        manuscript_id, tuple(), new_text_line
                                    ),
                                ),
                            ),
                        ),
                        is_second_line_of_parallelism,
                        is_beginning_of_section,
                    )
                },
            ),
            user,
        )
        == updated_chapter
    )


def test_update_lines_raises_exception_if_invalid_signs(
    corpus, text_repository, bibliography, when
) -> None:
    lines = LinesUpdate([], set(), dict(enumerate(CHAPTER.lines)))
    when(text_repository).find_chapter(CHAPTER.id_).thenReturn(
        CHAPTER_WITHOUT_DOCUMENTS
    )
    expect_bibliography(bibliography, when)

    with pytest.raises(DataError):
        corpus.update_lines(CHAPTER.id_, lines, ANY_USER)
