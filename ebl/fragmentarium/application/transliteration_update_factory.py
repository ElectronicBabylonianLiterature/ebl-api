from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.application.signs_visitor import SignsVisitor
from ebl.transliteration.domain.atf import Atf, WORD_SEPARATOR
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.transliteration.domain.text import TextLine


class TransliterationUpdateFactory:
    def __init__(self, sing_repository: SignRepository):
        self._sing_repository = sing_repository

    def create(self, atf: Atf, notes: str = "") -> TransliterationUpdate:
        text = parse_atf_lark(atf)
        signs = "\n".join(
            self._map_line(line)
            for line in text.lines if isinstance(line, TextLine)
        )
        return TransliterationUpdate(text, notes, signs)

    def _map_line(self, line: TextLine) -> str:
        visitor = SignsVisitor(self._sing_repository)
        for token in line.content:
            token.accept(visitor)
        return WORD_SEPARATOR.join(visitor.result)
