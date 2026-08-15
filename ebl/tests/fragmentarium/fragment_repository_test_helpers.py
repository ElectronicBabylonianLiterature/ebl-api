from typing import List

from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.application.signs_visitor import SignsVisitor
from ebl.transliteration.domain.transliteration_query import TransliterationQuery


COLLECTION = "fragments"
JOINS_COLLECTION = "joins"
SCHEMA = FragmentSchema()


def create_transliteration_query_lines(
    transliteration: str, sign_repository: SignRepository
) -> List[str]:
    return [
        TransliterationQuery(string=line, visitor=SignsVisitor(sign_repository)).regexp
        for line in transliteration.split("\n")
    ]
