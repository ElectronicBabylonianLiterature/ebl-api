from typing import Optional, cast
from lark import Tree
from ebl.transliteration.domain.atf_parsers.lark_parser_errors import (
    LINE_PARSE_ERRORS,
)
from ebl.transliteration.domain.atf_parsers.lark_parser import validate_line
from ebl.transliteration.domain.line import ControlLine, Line
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION
from ebl.fragmentarium.application.transliteration_update_factory import (
    TransliterationUpdateFactory,
)
from ebl.app import create_context
from ebl.transliteration.domain.line_transformer import LineTransformer
from ebl.transliteration.domain.text import Text
from ebl.atf_importer.domain.legacy_atf_visitor import (
    LegacyAtfVisitor,
)


class LegacyAtfLineValidator:
    transliteration_factory: Optional[TransliterationUpdateFactory] = None
    legacy_visitor = LegacyAtfVisitor()

    def __init__(self):
        if LegacyAtfLineValidator.transliteration_factory is None:
            LegacyAtfLineValidator.transliteration_factory = (
                create_context().get_transliteration_update_factory()
            )

    def validate_text_line(self, line_tree: Tree) -> Optional[Exception]:
        try:
            self.legacy_visitor.visit(line_tree)
            line = cast(Line, LineTransformer().transform(line_tree))
            validate_line(line)
            control_line = ControlLine(
                prefix="&",
                content="P000001 = X.1",
            )
            assert self.transliteration_factory is not None
            self.transliteration_factory.create_from_text(
                Text((control_line, line), ATF_PARSER_VERSION)
            )
            return None
        except LINE_PARSE_ERRORS as error:
            return error
