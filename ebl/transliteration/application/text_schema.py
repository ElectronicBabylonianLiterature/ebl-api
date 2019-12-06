from marshmallow import Schema, fields, post_load

from ebl.transliteration.application.line_schemas import dump_lines, load_lines
from ebl.transliteration.domain.atf import DEFAULT_ATF_PARSER_VERSION
from ebl.transliteration.domain.text import Text


class TextSchema(Schema):
    lines = fields.Function(
        lambda text: dump_lines(text.lines), load_lines, required=True
    )
    parser_version = fields.String(missing=DEFAULT_ATF_PARSER_VERSION)

    @post_load
    def make_text(self, data, **kwargs):
        return Text.of_iterable(data["lines"], data["parser_version"])
