from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.application.signs_visitor import SignsVisitor
from ebl.transliteration.domain.atf import Atf, WORD_SEPARATOR
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
from ebl.transliteration.domain.text import TextLine


class TransliterationUpdateFactory:
    def __init__(self, sign_repository: SignRepository):
        self._sign_repository = sign_repository

    def create(self, atf: Atf) -> TransliterationUpdate:
        text = parse_atf_lark(atf)
        signs = "\n".join(self._map_line(line) for line in text.text_lines)
        return TransliterationUpdate(text, signs)

    def _map_line(self, line: TextLine) -> str:
        visitor = SignsVisitor(self._sign_repository)
        line.accept(visitor)
        return WORD_SEPARATOR.join(visitor.result_string)
