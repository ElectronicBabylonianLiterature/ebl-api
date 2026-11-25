import attr

from ebl.corpus.application.lemmatization import (
    ChapterLemmatization,
    LineVariantLemmatization,
)
from ebl.dictionary.domain.word import WordId
from ebl.lemmatization.domain.lemmatization import LemmatizationToken
from ebl.tests.corpus.corpus_test_support import (
    CHAPTER,
    CHAPTER_WITHOUT_DOCUMENTS,
    UpdateDependencies,
    expect_chapter_update,
    expect_find_and_update_chapter,
)
from ebl.tests.corpus.lemmatized_chapter_support import lemmatize_first_line


def test_update_chapter(corpus, update_dependencies: UpdateDependencies) -> None:
    updated_chapter = attr.evolve(CHAPTER, version="New Version")
    expect_chapter_update(
        update_dependencies, CHAPTER_WITHOUT_DOCUMENTS, updated_chapter
    )

    corpus.update_chapter(
        CHAPTER_WITHOUT_DOCUMENTS.id_,
        CHAPTER_WITHOUT_DOCUMENTS,
        updated_chapter,
        update_dependencies.user,
    )


def test_updating_manuscript_lemmatization(
    corpus, update_dependencies: UpdateDependencies
) -> None:
    updated_chapter = lemmatize_first_line(CHAPTER)
    expect_find_and_update_chapter(
        update_dependencies, CHAPTER_WITHOUT_DOCUMENTS, updated_chapter
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
                    LemmatizationToken("...]-buāru#", ()),
                ),
                ((LemmatizationToken("ku-[nu-ši]", (WordId("aklu I"),)),),),
            ),
        ),
    )
    assert (
        corpus.update_manuscript_lemmatization(
            CHAPTER.id_, lemmatization, update_dependencies.user
        )
        == updated_chapter
    )
