from typing import Optional, Type
from lark import Tree
from ebl.transliteration.domain.atf_parsers.lark_parser_errors import PARSE_ERRORS
from ebl.transliteration.domain.transliteration_error import TransliterationError
from ebl.transliteration.domain.atf_parsers.lark_parser import validate_line
from ebl.transliteration.domain.line import ControlLine
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
    transliteration_factory: TransliterationUpdateFactory = (
        create_context().get_transliteration_update_factory()
    )
    legacy_visitor = LegacyAtfVisitor()

    def validate_text_line(self, line_tree: Tree) -> Optional[Type[Exception]]:
        try:
            self.legacy_visitor.visit(line_tree)
            line_tree = LineTransformer().transform(line_tree)
            validate_line(line_tree)
            control_line = ControlLine(
                prefix="&",
                content="P000001 = BM.1",
            )
            self.transliteration_factory.create_from_text(
                Text((control_line, line_tree), ATF_PARSER_VERSION)
            )
            return None
        except (*PARSE_ERRORS, TransliterationError) as error:
            return error
