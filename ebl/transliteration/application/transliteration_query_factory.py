from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.transliteration_query import TransliterationQuery


class TransliterationQueryFactory:
    def __init__(self, sign_repository: SignRepository) -> None:
        self._sign_repository = sign_repository

    @staticmethod
    def create_empty() -> TransliterationQuery:
        return TransliterationQuery(string="", sign_repository=None)

    def create(self, transliteration: str) -> TransliterationQuery:
        return TransliterationQuery(
            string=transliteration, sign_repository=self._sign_repository
        )
