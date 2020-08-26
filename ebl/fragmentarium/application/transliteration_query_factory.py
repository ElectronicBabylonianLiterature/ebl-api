from typing import Sequence, cast

from ebl.fragmentarium.domain.transliteration_query import TransliterationQuery
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.application.signs_visitor import SignsVisitor
from ebl.transliteration.domain.lark_parser import parse_line
from ebl.transliteration.domain.text_line import TextLine


class TransliterationQueryFactory:
    def __init__(self, sign_repositoy: SignRepository) -> None:
        self._sign_repositoy = sign_repositoy

    def create(self, transliteration: str) -> TransliterationQuery:
        signs = [
            self._create_signs(line)
            for line
            in transliteration.split("\n")
        ]
        return TransliterationQuery(signs)

    def _create_signs(self, line: str) -> Sequence[str]:
        parsed_line = cast(TextLine, parse_line(f"1. {line}"))
        visitor = SignsVisitor(self._sign_repositoy)
        for token in parsed_line.content:
            token.accept(visitor)

        return visitor.result
