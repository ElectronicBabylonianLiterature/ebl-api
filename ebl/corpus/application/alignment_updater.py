from typing import Sequence

import attr

from ebl.corpus.application.line_updater import (
    EachLineUpdater,
    LineUpdater,
    require_count,
    require_manuscript_token_counts,
)
from ebl.corpus.domain.alignment import (
    Alignment,
    LineAlignment,
    ManuscriptLineAlignment,
)
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.line_variant import LineVariant
from ebl.corpus.domain.manuscript_line import ManuscriptLine
from ebl.transliteration.domain.alignment import AlignmentError


def _align_manuscript_line(
    manuscript_line: ManuscriptLine, alignment: ManuscriptLineAlignment
) -> ManuscriptLine:
    return attr.evolve(
        manuscript_line,
        line=manuscript_line.line.update_alignment(alignment.alignment),
        omitted_words=alignment.omitted_words,
    )


def _align_variant(
    variant: LineVariant, alignment: Sequence[ManuscriptLineAlignment]
) -> LineVariant:
    require_count(
        AlignmentError, "manuscripts", len(alignment), len(variant.manuscripts)
    )
    return attr.evolve(
        variant,
        manuscripts=tuple(
            _align_manuscript_line(manuscript_line, alignment[index])
            for index, manuscript_line in enumerate(variant.manuscripts)
        ),
    ).set_alignment_flags()


def align_line(
    line: Line, alignment: Sequence[Sequence[ManuscriptLineAlignment]]
) -> Line:
    require_count(AlignmentError, "variants", len(alignment), len(line.variants))
    return attr.evolve(
        line,
        variants=tuple(
            _align_variant(variant, alignment[index])
            for index, variant in enumerate(line.variants)
        ),
    )


class AlignmentUpdater(EachLineUpdater):
    def __init__(self, alignment: Alignment) -> None:
        super().__init__()
        self._alignment = alignment

    def _validate_chapter(self, chapter: Chapter) -> None:
        require_count(
            AlignmentError,
            "lines",
            self._alignment.get_number_of_lines(),
            len(chapter.lines),
        )

    def _update_line(self, index: int, line: Line) -> Line:
        return align_line(line, self._alignment.get_line(index))


class LineAlignmentUpdater(LineUpdater):
    def __init__(self, alignment: LineAlignment) -> None:
        super().__init__(alignment.index)
        self._alignment = alignment

    def _update_line(self, line: Line) -> Line:
        require_manuscript_token_counts(
            AlignmentError,
            line,
            [
                [len(manuscript.alignment) for manuscript in variant]
                for variant in self._alignment.variants
            ],
        )
        return align_line(line, self._alignment.variants)
