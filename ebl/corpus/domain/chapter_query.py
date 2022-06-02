import attr
from typing import Mapping, Sequence
from ebl.corpus.domain.line import Line
from ebl.transliteration.domain.text_line import TextLine
from ebl.corpus.domain.manuscript import Manuscript


@attr.s(auto_attribs=True, frozen=True)
class ChapterQueryColophonLines:
    manuscript_colophon_lines: Mapping[int, Sequence[int]] = {}

    def add_manuscript_line(self, manuscript_id: int, line_index: int):
        self.manuscript_colophon_lines.setdefault(manuscript_id, []).append(line_index)

    def get_matching_lines(
        self, manuscripts: Sequence[Manuscript]
    ) -> Mapping[int, Sequence[TextLine]]:
        matching_colophon_lines = {}
        for manuscript in manuscripts:
            if manuscript.id in self.manuscript_colophon_lines:
                matching_colophon_lines = {
                    **matching_colophon_lines,
                    **self.select_matching_colophon_lines_filtered(
                        manuscript.id,
                        manuscript.colophon.lines,
                    ),
                }
        return matching_colophon_lines

    def select_matching_colophon_lines_filtered(
        self,
        manuscript_id: int,
        manuscript_colophon_lines: Sequence[Line],
    ) -> Mapping[int, Sequence[TextLine]]:
        colophon_lines = [
            line for line in manuscript_colophon_lines if isinstance(line, TextLine)
        ]
        return {
            manuscript_id: [
                colophon_lines[idx]
                for idx in self.colophon_lines_in_query[manuscript_id]
                if idx < len(colophon_lines)
            ]
        }
