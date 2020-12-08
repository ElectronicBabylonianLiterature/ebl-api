from typing import Sequence

import attr

from ebl.transliteration.domain.alignment import AlignmentToken
from ebl.corpus.domain.text import ManuscriptLine


@attr.s(auto_attribs=True, frozen=True)
class ManuscriptLineAlignment:
    alignment: Sequence[AlignmentToken]
    omitted_words: Sequence[int] = tuple()

    def apply(self, manuscript_line: ManuscriptLine) -> ManuscriptLine:
        return attr.evolve(
            manuscript_line,
            line=manuscript_line.line.update_alignment(self.alignment),
            omitted_words=self.omitted_words,
        )


@attr.s(auto_attribs=True, frozen=True)
class Alignment:
    _lines: Sequence[Sequence[ManuscriptLineAlignment]]

    def get_line(self, line_index: int) -> Sequence[ManuscriptLineAlignment]:
        return self._lines[line_index]

    def get_manuscript_line(
        self, line_index: int, manuscript_index: int
    ) -> ManuscriptLineAlignment:
        return self.get_line(line_index)[manuscript_index]

    def get_number_of_lines(self) -> int:
        return len(self._lines)

    def get_number_of_manuscripts(self, line_index: int) -> int:
        return len(self.get_line(line_index))
