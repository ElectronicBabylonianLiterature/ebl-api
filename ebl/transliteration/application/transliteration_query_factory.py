from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.transliteration_query import (
    TransliterationQuery,
    TransliterationQueryEmpty,
)
from ebl.transliteration.domain.lark_parser import PARSE_ERRORS
from ebl.errors import DataError
from ebl.transliteration.domain.tokens import TokenVisitor
from ebl.transliteration.application.signs_visitor import SignsVisitor


class TransliterationQueryFactory:
    def __init__(self, sign_repository: SignRepository) -> None:
        self.visitor = SignsVisitor(sign_repository)

    @staticmethod
    def create_empty() -> TransliterationQuery:
        return TransliterationQueryEmpty()

    def create(self, string: str) -> TransliterationQuery:
        query = TransliterationQuery(string=string, visitor=self.visitor)
        try:
            query.regexp
            return query
        except PARSE_ERRORS:
            raise DataError("Invalid transliteration query.")
