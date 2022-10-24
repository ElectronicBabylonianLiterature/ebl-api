from typing import Sequence

from lark.lexer import Token
from lark.visitors import Transformer, v_args

from ebl.bibliography.domain.reference import BibliographyId
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.line import ControlLine, EmptyLine
from ebl.transliteration.domain.markup import (
    BibliographyPart,
    EmphasisPart,
    LanguagePart,
    MarkupPart,
    ParagraphSeparatorPart,
    StringPart,
)
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.tokens import Token as EblToken


class IntroductionLineTransformer(Transformer):
    @v_args(inline=True)
    def ebl_atf_introduction__language_part(
        self, language: Token, transliteration: Sequence[EblToken]
    ) -> LanguagePart:
        return LanguagePart.of_transliteration(
            Language.of_atf(f"%{language}"), transliteration
        )

    @v_args(inline=True)
    def ebl_atf_introduction__emphasis_part(self, text: str) -> EmphasisPart:
        return EmphasisPart(text)

    @v_args(inline=True)
    def ebl_atf_introduction__string_part(self, text: str) -> StringPart:
        return StringPart(text)

    @v_args(inline=True)
    def ebl_atf_introduction__text(self, children) -> str:
        return "".join(children)
    
    def ebl_atf_introduction__text(self, children):
        return tokens_to_value_tokens(children)

    @v_args(inline=True)
    def ebl_atf_introduction__bibliography_part(self, id_, pages) -> BibliographyPart:
        return BibliographyPart.of(
            BibliographyId("".join(id_.children)), "".join(pages.children)
        )

    def ebl_atf_introduction__paragraph_part(self, _) -> ParagraphSeparatorPart:
        return ParagraphSeparatorPart()

    def introduction(self, children):
        return tuple(children)
