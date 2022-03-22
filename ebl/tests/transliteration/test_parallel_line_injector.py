import attr
import pytest
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.tests.factories.parallel_line import (
    ParallelFragmentFactory,
    ParallelTextFactory,
)

from ebl.transliteration.domain.parallel_line import ParallelFragment, ParallelText


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


def test_inject_other_lines(parallel_line_injector):
    lines = tuple(
        line
        for line in TransliteratedFragmentFactory.build().text.lines
        if not isinstance(line, (ParallelFragment, ParallelText))
    )
    assert parallel_line_injector.inject(lines) == lines
