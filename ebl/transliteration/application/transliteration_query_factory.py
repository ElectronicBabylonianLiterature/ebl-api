from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.transliteration_query import TransliterationQuery
from ebl.transliteration.domain.lark_parser import PARSE_ERRORS
from ebl.errors import DataError


class TransliterationQueryFactory:
    def __init__(self, sign_repository: SignRepository) -> None:
        self._sign_repository = sign_repository

    @staticmethod
    def create_empty() -> TransliterationQuery:
        return TransliterationQuery(string="", sign_repository=None)

    def create(self, transliteration: str) -> TransliterationQuery:
        query = TransliterationQuery(
            string=transliteration, sign_repository=self._sign_repository
        )
        try:
            query.regexp
            return query
        except PARSE_ERRORS:
            raise DataError("Invalid transliteration query.")
