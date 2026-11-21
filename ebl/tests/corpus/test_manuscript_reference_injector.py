import attr
import pytest

from ebl.bibliography.application.bibliography import Bibliography
from ebl.corpus.application.manuscript_reference_injector import (
    ManuscriptReferenceInjector,
    inject_references_to_submitted_manuscripts,
)
from ebl.corpus.domain.chapter import Chapter
from ebl.errors import DataError, Defect
from ebl.tests.corpus.outline_support import create_outline_chapter
from ebl.tests.corpus.support import allow_references
from ebl.tests.factories.bibliography import ReferenceFactory


def remove_documents(chapter: Chapter) -> Chapter:
    return attr.evolve(
        chapter,
        manuscripts=tuple(
            attr.evolve(
                manuscript,
                references=tuple(
                    attr.evolve(reference, document=None)
                    for reference in manuscript.references
                ),
                old_sigla=tuple(
                    attr.evolve(
                        old_siglum,
                        reference=attr.evolve(old_siglum.reference, document=None),
                    )
                    for old_siglum in manuscript.old_sigla
                ),
            )
            for manuscript in chapter.manuscripts
        ),
    )


def read_chapter(injector: ManuscriptReferenceInjector) -> Chapter:
    return injector.chapter


@pytest.fixture
def chapter(bibliography: Bibliography) -> Chapter:
    chapter = create_outline_chapter()
    allow_references(chapter, bibliography)
    return chapter


def test_chapter_is_a_defect_before_a_chapter_was_visited(
    bibliography: Bibliography,
) -> None:
    with pytest.raises(Defect, match="before a chapter was visited"):
        read_chapter(ManuscriptReferenceInjector(bibliography))


def test_visiting_a_line_does_not_set_the_chapter(
    bibliography: Bibliography, chapter: Chapter
) -> None:
    injector = ManuscriptReferenceInjector(bibliography)

    injector.visit(chapter.lines[0])

    with pytest.raises(Defect):
        read_chapter(injector)


def test_visiting_a_chapter_injects_the_documents(
    bibliography: Bibliography, chapter: Chapter
) -> None:
    injector = ManuscriptReferenceInjector(bibliography)

    injector.visit(remove_documents(chapter))

    assert read_chapter(injector) == chapter


def test_inject_references_to_submitted_manuscripts(
    bibliography: Bibliography, chapter: Chapter
) -> None:
    manuscripts = remove_documents(chapter).manuscripts

    assert manuscripts != chapter.manuscripts
    assert (
        inject_references_to_submitted_manuscripts(bibliography, manuscripts)
        == chapter.manuscripts
    )


def test_inject_references_to_no_manuscripts(bibliography: Bibliography) -> None:
    assert inject_references_to_submitted_manuscripts(bibliography, ()) == ()


def test_inject_unknown_references_to_submitted_manuscripts(
    bibliography: Bibliography, chapter: Chapter
) -> None:
    unknown_reference = ReferenceFactory.build()
    manuscripts = (
        chapter.manuscripts[0],
        attr.evolve(chapter.manuscripts[1], references=(unknown_reference,)),
    )

    with pytest.raises(DataError, match=f"{unknown_reference.id} not found"):
        inject_references_to_submitted_manuscripts(bibliography, manuscripts)
