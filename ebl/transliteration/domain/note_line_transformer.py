from typing import Sequence

from lark.lexer import Token
from lark.visitors import Transformer, v_args

from ebl.bibliography.domain.reference import BibliographyId
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.markup import (
    BibliographyPart,
    EmphasisPart,
    LanguagePart,
    MarkupPart,
    StringPart,
    UrlPart,
)
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.tokens import Token as EblToken


class MarkupTransformer(Transformer):

    def __init__(self):
        for method in [method for method in dir(self) if "ebl_atf_note_line" in method]:
            setattr(self, f"ebl_atf_at_line__{method}", getattr(self, method))
            setattr(self, f"ebl_atf_translation_line__{method}", getattr(self, method))

    def markup(self, children) -> Sequence[MarkupPart]:
        return tuple(children)

    def ebl_atf_note_line__markup(self, children) -> Sequence[MarkupPart]:
        return tuple(children)

    @v_args(inline=True)
    def ebl_atf_note_line__language_part(
        self, language: Token, transliteration: Sequence[EblToken]
    ) -> LanguagePart:
        return LanguagePart.of_transliteration(
            Language.of_atf(f"%{language}"), transliteration.children
        )

    @v_args(inline=True)
    def ebl_atf_note_line__emphasis_part(self, text: str) -> EmphasisPart:
        return EmphasisPart(text)

    @v_args(inline=True)
    def ebl_atf_note_line__string_part(self, text: str) -> StringPart:
        return StringPart(text)

    @v_args(inline=True)
    def ebl_atf_note_line__bibliography_part(self, id_, pages=None) -> BibliographyPart:
        return BibliographyPart.of(
            BibliographyId("".join(id_.children)),
            "".join(pages.children) if pages else "",
        )

    def ebl_atf_note_line__note_text(self, children) -> str:
        return "".join(children)

    @v_args(inline=True)
    def ebl_atf_note_line__url_part(self, url: str, note_text="") -> UrlPart:
        return UrlPart(note_text, url)

    def ebl_atf_note_line__url(self, children) -> str:
        return "".join(children)


class NoteLineTransformer(MarkupTransformer):

    def __init__(self):
        super(MarkupTransformer, self).__init__()

    def note_line(self, children: Sequence[MarkupPart]) -> NoteLine:
        return NoteLine(children)
