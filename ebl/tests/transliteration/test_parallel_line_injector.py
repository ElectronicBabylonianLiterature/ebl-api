import attr
import pytest
from ebl.errors import NotFoundError
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.tests.factories.ids import ChapterNameFactory
from ebl.tests.factories.parallel_line import (
    ParallelFragmentFactory,
    ParallelTextFactory,
)

from ebl.transliteration.domain.parallel_line import (
    ChapterName,
    ParallelFragment,
    ParallelText,
)


@pytest.mark.parametrize("exists", [True, False])
def test_inject_parallel_fragment(
    parallel_repository, parallel_line_injector, when, exists
):
    line: ParallelFragment = ParallelFragmentFactory.build()
    when(parallel_repository).fragment_exists(line.museum_number).thenReturn(exists)
    assert parallel_line_injector.inject([line]) == (attr.evolve(line, exists=exists),)


@pytest.mark.parametrize("exists", [True, False])
def test_inject_parallel_text(
    parallel_repository, parallel_line_injector, when, exists
):
    line: ParallelText = ParallelTextFactory.build()
    when(parallel_repository).chapter_exists(line.text, line.chapter).thenReturn(exists)
    assert parallel_line_injector.inject([line]) == (attr.evolve(line, exists=exists),)


def test_inject_parallel_text_implicit_chapter(
    parallel_repository, parallel_line_injector, when
):
    chapter: ChapterName = ChapterNameFactory.build()
    line: ParallelText = ParallelTextFactory.build(chapter=None)
    when(parallel_repository).find_implicit_chapter(line.text).thenReturn(chapter)
    assert parallel_line_injector.inject([line]) == (
        attr.evolve(line, exists=True, implicit_chapter=chapter),
    )


def test_inject_parallel_text_implicit_chapter_not_found(
    parallel_repository, parallel_line_injector, when
):
    line: ParallelText = ParallelTextFactory.build(chapter=None)
    when(parallel_repository).find_implicit_chapter(line.text).thenRaise(NotFoundError)
    assert parallel_line_injector.inject([line]) == (attr.evolve(line, exists=False),)


def test_inject_other_lines(parallel_line_injector):
    lines = tuple(
        line
        for line in TransliteratedFragmentFactory.build().text.lines
        if not isinstance(line, (ParallelFragment, ParallelText))
    )
    assert parallel_line_injector.inject(lines) == lines


def test_inject_transliteration(parallel_line_injector, parallel_repository, when):
    transliteration = TransliteratedFragmentFactory.build().text
    when(parallel_repository).chapter_exists(...).thenReturn(True)
    when(parallel_repository).fragment_exists(...).thenReturn(True)
    assert parallel_line_injector.inject_transliteration(
        transliteration
    ) == attr.evolve(
        transliteration, lines=parallel_line_injector.inject(transliteration.lines)
    )
