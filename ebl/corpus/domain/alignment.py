from typing import Sequence

import attr

from ebl.transliteration.domain.alignment import AlignmentToken


@attr.s(auto_attribs=True, frozen=True)
class ManuscriptLineAlignment:
    alignment: Sequence[AlignmentToken]
    omitted_words: Sequence[int] = ()


@attr.s(auto_attribs=True, frozen=True)
class Alignment:
    _lines: Sequence[Sequence[Sequence[ManuscriptLineAlignment]]]

    def get_line(self, line_index: int) -> Sequence[Sequence[ManuscriptLineAlignment]]:
        return self._lines[line_index]

    def get_variant(
        self, line_index: int, variant_index: int
    ) -> Sequence[ManuscriptLineAlignment]:
        return self.get_line(line_index)[variant_index]

    def get_manuscript_line(
        self, line_index: int, variant_index: int, manuscript_index: int
    ) -> ManuscriptLineAlignment:
        return self.get_variant(line_index, variant_index)[manuscript_index]

    def get_number_of_lines(self) -> int:
        return len(self._lines)

    def get_number_of_variants(self, line_index: int) -> int:
        return len(self.get_line(line_index))

    def get_number_of_manuscripts(self, line_index: int, variant_index: int) -> int:
        return len(self.get_variant(line_index, variant_index))
