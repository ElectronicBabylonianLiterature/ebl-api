from typing import Sequence

from lark.lexer import Token  # pyre-ignore[21]
from lark.visitors import Transformer, v_args  # pyre-ignore[21]

from ebl.bibliography.domain.reference import BibliographyId
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.note_line import (
    BibliographyPart,
    EmphasisPart,
    LanguagePart,
    NoteLine,
    NotePart,
    StringPart,
)


class NoteLineTransformer(Transformer):  # pyre-ignore[11]
    def note_line(self, children: Sequence[NotePart]) -> NoteLine:
        return NoteLine(children)

    @v_args(inline=True)  # pyre-ignore[56]
    def ebl_atf_text_line__language_part(
        self, language: Token, transliteration: Sequence[Token]  # pyre-ignore[11]
    ) -> LanguagePart:
        return LanguagePart.of_transliteration(
            Language.of_atf(f"%{language}"), transliteration
        )

    @v_args(inline=True)  # pyre-ignore[56]
    def ebl_atf_text_line__emphasis_part(self, text: str) -> EmphasisPart:
        return EmphasisPart(text)

    @v_args(inline=True)  # pyre-ignore[56]
    def ebl_atf_text_line__string_part(self, text: str) -> StringPart:
        return StringPart(text)

    @v_args(inline=True)  # pyre-ignore[56]
    def ebl_atf_text_line__bibliography_part(self, id_, pages) -> BibliographyPart:
        return BibliographyPart.of(
            BibliographyId("".join(id_.children)), "".join(pages.children)
        )

    def ebl_atf_text_line__note_text(self, children: Sequence[Token]) -> str:
        return "".join(children)
