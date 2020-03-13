from typing import Sequence

from lark.lexer import Token
from lark.visitors import Transformer, v_args

from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.note_line import (
    EmphasisPart,
    LanguagePart,
    NoteLine,
    NotePart,
    StringPart,
)


class NoteLineTransformer(Transformer):
    def note_line(self, children: Sequence[NotePart]) -> NoteLine:
        return NoteLine(children)

    @v_args(inline=True)
    def ebl_atf_note_line__language_part(
        self, language: Token, text: str
    ) -> LanguagePart:
        return LanguagePart(text, Language.of_atf(f"%{language}"))

    @v_args(inline=True)
    def ebl_atf_note_line__emphasis_part(self, text: str) -> EmphasisPart:
        return EmphasisPart(text)

    @v_args(inline=True)
    def ebl_atf_note_line__string_part(self, text: str) -> StringPart:
        return StringPart(text)

    def ebl_atf_note_line__note_text(self, children: Sequence[Token]) -> str:
        return "".join(children)
