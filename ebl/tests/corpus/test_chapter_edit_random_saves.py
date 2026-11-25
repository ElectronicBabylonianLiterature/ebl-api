from random import Random
from typing import Callable, List

import attr
import dictdiffer
import pytest

from ebl.corpus.application.chapter_changelog import dump_chapter_document
from ebl.corpus.application.chapter_edit_writer import ChapterEditWriter
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_revision import LEGACY_REVISION
from ebl.tests.corpus.chapter_change_cases import SEEDS
from ebl.tests.corpus.line_annotation_support import create_annotation_chapter
from ebl.tests.corpus.lines_edit_support import find_chapter_changelog_entries
from ebl.tests.corpus.random_save_support import create_random_save, try_save
from ebl.tests.corpus.reference_save_support import ChapterCopies

STEPS = 10


@pytest.mark.parametrize("seed", SEEDS)
def test_random_saves_store_what_the_full_path_stores(
    writer: ChapterEditWriter,
    reference_writer: ChapterEditWriter,
    copies: ChapterCopies,
    store_editable_chapter: Callable[[Chapter], Chapter],
    seed: int,
) -> None:
    random = Random(seed)
    chapter = store_editable_chapter(create_annotation_chapter())
    sibling = copies.create_sibling(chapter)
    current = writer.find_chapter(chapter.id_)
    revisions = [LEGACY_REVISION, LEGACY_REVISION]
    errors: List[str] = []
    unchanged = 0

    for step in range(STEPS):
        save = create_random_save(random, current, step)
        saved, error = try_save(save, writer, chapter.id_, revisions[0])
        reference_saved, reference_error = try_save(
            save, reference_writer, sibling.id_, revisions[1]
        )

        assert error == reference_error
        copies.assert_equal(chapter, sibling)
        if saved is None or reference_saved is None:
            errors.append(error)
            continue
        if saved.chapter == current:
            assert [saved.revision, reference_saved.revision] == revisions
            unchanged += 1
            continue
        entry = find_chapter_changelog_entries(copies.database)[-2]
        assert dictdiffer.patch(
            entry["diff"], dump_chapter_document(current)
        ) == dump_chapter_document(saved.chapter)
        assert saved.chapter == attr.evolve(reference_saved.chapter, name=chapter.name)
        assert saved.chapter == writer.find_chapter(chapter.id_)
        current = saved.chapter
        revisions = [saved.revision, reference_saved.revision]

    assert len(find_chapter_changelog_entries(copies.database)) == 2 * (
        STEPS - len(errors) - unchanged
    )
    assert len(errors) < STEPS / 2
