import attr
from typing import Mapping, Sequence
from marshmallow import Schema, fields, post_load
from ebl.corpus.domain.line import Line
from ebl.transliteration.domain.text_line import TextLine
from ebl.corpus.domain.manuscript import Manuscript
from ebl.transliteration.domain.text_line import TextLine


@attr.s(auto_attribs=True, frozen=True)
class ChapterQueryColophonLines:
    colophon_lines_in_query: Mapping[int, Sequence[int]] = dict()

    def get_matching_lines(
        self, manuscripts: Sequence[Manuscript]
    ) -> Mapping[int, Sequence[TextLine]]:
        matching_colophon_lines = {}
        for manuscript in manuscripts:
            if manuscript.id in self.colophon_lines_in_query:
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


class ColophonIndexesSchema(Schema):
    index = fields.Int


class ChapterQueryColophonLinesSchema(Schema):
    colophon_lines_in_query = fields.Mapping(
        keys=fields.Int(),
        values=fields.List(
            fields.Int()
        ),
        load_default=dict(),
    )

    @post_load
    def make_colophon_lines(self, data: dict, **kwargs) -> ChapterQueryColophonLines:
        #print(data, kwargs)
        return ChapterQueryColophonLines(data)
