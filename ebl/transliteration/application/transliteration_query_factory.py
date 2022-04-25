from typing import Sequence, cast

from ebl.errors import DataError
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.application.signs_visitor import SignsVisitor
from ebl.transliteration.domain.lark_parser import PARSE_ERRORS, parse_line
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.transliteration_query import TransliterationQuery


class TransliterationQueryFactory:
    def __init__(self, sign_repositoy: SignRepository) -> None:
        self._sign_repositoy = sign_repositoy

    @staticmethod
    def create_empty() -> TransliterationQuery:
        return TransliterationQuery([])

    def create(self, transliteration: str) -> TransliterationQuery:
        signs = [self._create_signs(line) for line in transliteration.split("\n")]
        return TransliterationQuery(signs)

    def _create_signs(self, line: str) -> Sequence[str]:
        visitor = SignsVisitor(self._sign_repositoy)
        self._parse_line(line).accept(visitor)

        return visitor.result

    def _parse_line(self, line: str) -> TextLine:
        try:
            return cast(TextLine, parse_line(f"1. {line}"))
        except PARSE_ERRORS:
            raise DataError("Invalid transliteration query.")
