from typing import Sequence
from lark import Tree
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

MARKUP_PREFIXES = [
    "ebl_atf_at_line",
    "ebl_atf_manuscript_line",
    "ebl_atf_translation_line",
]


class MarkupTransformer(Transformer):
    def __init__(self):
        super().__init__()
        for method in [method for method in dir(self) if "ebl_atf_note_line" in method]:
            for prefix in MARKUP_PREFIXES:
                setattr(self, f"{prefix}__{method}", getattr(self, method))

    def markup(self, children) -> Sequence[MarkupPart]:
        return tuple(children)

    def ebl_atf_note_line__markup(self, children) -> Sequence[MarkupPart]:
        return tuple(children)

    @v_args(inline=True)
    def ebl_atf_note_line__language_part(
        self, language: Token, transliteration: Tree
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


NOTE_LINE_PREFIXES = [
    "ebl_atf_at_line",
    "ebl_atf_manuscript_line",
    "ebl_atf_translation_line",
]


class NoteLineTransformer(MarkupTransformer):
    def __init__(self):
        super().__init__()
        for method in [method for method in dir(self) if "note_line" in method]:
            for prefix in NOTE_LINE_PREFIXES:
                setattr(self, f"{prefix}__{method}", getattr(self, method))

    def note_line(self, children: Sequence[MarkupPart]) -> NoteLine:
        return NoteLine(children)
