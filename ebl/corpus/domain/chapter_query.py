import attr
from typing import Mapping, Sequence, Union
from marshmallow import Schema, fields, post_load
from ebl.transliteration.domain.text_line import TextLine, L
from ebl.corpus.domain.manuscript import Manuscript


@attr.s(auto_attribs=True, frozen=True)
class ChapterQueryColophonLines:
    colophon_lines_in_query: Mapping[str, Sequence[int]] = {}

    def get_matching_lines(
        self, manuscripts: Sequence[Manuscript]
    ) -> Mapping[int, Sequence[TextLine]]:
        matching_colophon_lines = {}
        for manuscript in manuscripts:
            if str(manuscript.id) in self.colophon_lines_in_query:
                matching_colophon_lines = {
                    **matching_colophon_lines,
                    **self.select_matching_colophon_lines_filtered(
                        manuscript.id,
                        self.filter_text_lines(manuscript.colophon.lines),
                    ),
                }
        return matching_colophon_lines

    def select_matching_colophon_lines_filtered(
        self,
        manuscript_id: int,
        colophon_lines: Sequence[TextLine],
    ) -> Mapping[int, Sequence[TextLine]]:
        return {
            manuscript_id: [
                colophon_lines[idx]
                for idx in self.colophon_lines_in_query[str(manuscript_id)]
                if idx < len(colophon_lines)
            ]
        }

    def filter_text_lines(
        self, manuscript_colophon_lines: Sequence[Union["TextLine", L]]
    ) -> Sequence[TextLine]:
        return [
            line for line in manuscript_colophon_lines if isinstance(line, TextLine)
        ]


class ChapterQueryColophonLinesSchema(Schema):
    colophon_lines_in_query = fields.Dict(
        keys=fields.Str(),
        values=fields.List(fields.Int()),
        load_default={},
        data_key="colophonLinesInQuery",
    )

    @post_load
    def make_colophon_lines(self, data: dict, **kwargs) -> ChapterQueryColophonLines:
        return ChapterQueryColophonLines(data["colophon_lines_in_query"])
