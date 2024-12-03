from lark.visitors import Transformer, v_args

from ebl.transliteration.domain.enclosure_tokens import (
    AccidentalOmission,
    BrokenAway,
    Determinative,
    DocumentOrientedGloss,
    Erasure,
    IntentionalOmission,
    LinguisticGloss,
    PerhapsBrokenAway,
    PhoneticGloss,
    Removal,
)
from ebl.transliteration.domain.erasure_visitor import set_erasure_state
from ebl.transliteration.domain.atf_parsers.lark import tokens_to_value_tokens
from ebl.transliteration.domain.tokens import ErasureState


class EnclosureTransformer(Transformer):
    def ebl_atf_text_line__open_accidental_omission(self, _):
        return AccidentalOmission.open()

    def ebl_atf_text_line__close_accidental_omission(self, _):
        return AccidentalOmission.close()

    def ebl_atf_text_line__open_intentional_omission(self, _):
        return IntentionalOmission.open()

    def ebl_atf_text_line__close_intentional_omission(self, _):
        return IntentionalOmission.close()

    def ebl_atf_text_line__open_removal(self, _):
        return Removal.open()

    def ebl_atf_text_line__close_removal(self, _):
        return Removal.close()

    def ebl_atf_text_line__close_broken_away(self, _):
        return BrokenAway.close()

    def ebl_atf_text_line__open_broken_away(self, _):
        return BrokenAway.open()

    def ebl_atf_text_line__close_perhaps_broken_away(self, _):
        return PerhapsBrokenAway.close()

    def ebl_atf_text_line__open_perhaps_broken_away(self, _):
        return PerhapsBrokenAway.open()

    @v_args(inline=True)
    def ebl_atf_text_line__open_document_oriented_gloss(self, _):
        return DocumentOrientedGloss.open()

    @v_args(inline=True)
    def ebl_atf_text_line__close_document_oriented_gloss(self, _):
        return DocumentOrientedGloss.close()

    @v_args(inline=True)
    def ebl_atf_text_line__erasure(self, erased, over_erased):
        return self._transform_erasure(erased, over_erased)

    def _transform_erasure(self, erased, over_erased):
        return [
            Erasure.open(),
            *set_erasure_state(erased, ErasureState.ERASED),
            Erasure.center(),
            *set_erasure_state(over_erased, ErasureState.OVER_ERASED),
            Erasure.close(),
        ]


class GlossTransformer(Transformer):
    @v_args(inline=True)
    def ebl_atf_text_line__determinative(self, tree):
        tokens = tokens_to_value_tokens(tree.children)
        return Determinative.of(tokens)

    @v_args(inline=True)
    def ebl_atf_text_line__phonetic_gloss(self, tree):
        tokens = tokens_to_value_tokens(tree.children)
        return PhoneticGloss.of(tokens)

    @v_args(inline=True)
    def ebl_atf_text_line__linguistic_gloss(self, tree):
        tokens = tokens_to_value_tokens(tree.children)
        return LinguisticGloss.of(tokens)
