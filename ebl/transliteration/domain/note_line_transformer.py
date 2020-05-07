from typing import Sequence

from lark.lexer import Token  # pyre-ignore
from lark.visitors import Transformer, v_args

from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.note_line import (
    EmphasisPart,
    LanguagePart,
    NoteLine,
    NotePart,
    StringPart,
)


class NoteLineTransformer(Transformer):  # pyre-ignore[11]
    def note_line(self, children: Sequence[NotePart]) -> NoteLine:
        return NoteLine(children)

    @v_args(inline=True)
    def ebl_atf_text_line__language_part(
        self, language: Token, transliteration: Sequence[Token]  # pyre-ignore[11]
    ) -> LanguagePart:
        return LanguagePart.of_transliteration(
            Language.of_atf(f"%{language}"),
            transliteration
        )

    @v_args(inline=True)
    def ebl_atf_text_line__emphasis_part(self, text: str) -> EmphasisPart:
        return EmphasisPart(text)

    @v_args(inline=True)
    def ebl_atf_text_line__string_part(self, text: str) -> StringPart:
        return StringPart(text)

    def ebl_atf_text_line__note_text(self, children: Sequence[Token]) -> str:  # pyre-ignore[11]
        return "".join(children)
