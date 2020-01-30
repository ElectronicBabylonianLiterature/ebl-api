from functools import singledispatchmethod  # type: ignore
from typing import MutableSequence, Sequence, Type

import pydash
from lark.exceptions import ParseError, UnexpectedInput
from lark.lark import Lark
from lark.lexer import Token
from lark.tree import Tree
from lark.visitors import Transformer, v_args

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.atf import sub_index_to_int
from ebl.transliteration.domain.enclosure_tokens import (
    IntentionalOmission,
    BrokenAway,
    Determinative,
    DocumentOrientedGloss,
    Erasure,
    LinguisticGloss,
    AccidentalOmission,
    PerhapsBrokenAway,
    PhoneticGloss,
    Removal,
)
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.line import (
    ControlLine,
    EmptyLine,
    TextLine,
    LooseDollarLine,
    RulingDollarLine,
    ImageDollarLine,
    StrictDollarLine,
    ScopeContainer,
)
from ebl.transliteration.domain.sign_tokens import (
    CompoundGrapheme,
    Divider,
    Grapheme,
    Logogram,
    Number,
    Reading,
    UnclearSign,
    UnidentifiedSign,
)
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.tokens import (
    Column,
    CommentaryProtocol,
    Joiner,
    LanguageShift,
    LineContinuation,
    Tabulation,
    Token as EblToken,
    TokenVisitor,
    UnknownNumberOfSigns,
    ValueToken,
    Variant,
)
from ebl.transliteration.domain.transliteration_error import TransliterationError
from ebl.transliteration.domain.word_tokens import (
    ErasureState,
    InWordNewline,
    LoneDeterminative,
    Word,
)


class ErasureVisitor(TokenVisitor):
    def __init__(self, state: ErasureState):
        self._tokens: MutableSequence[EblToken] = []
        self._state: ErasureState = state

    @property
    def tokens(self) -> Sequence[EblToken]:
        return tuple(self._tokens)

    @singledispatchmethod
    def visit(self, token: EblToken) -> None:
        self._tokens.append(token)

    @visit.register
    def _visit_word(self, word: Word) -> None:
        self._tokens.append(word.set_erasure(self._state))


class TreeToSign(Transformer):
    @v_args(inline=True)
    def ebl_atf_text_line__unidentified_sign(self, flags):
        return UnidentifiedSign(flags)

    @v_args(inline=True)
    def ebl_atf_text_line__unclear_sign(self, flags):
        return UnclearSign(flags)

    @v_args(inline=True)
    def ebl_atf_text_line__unknown_number_of_signs(self, _):
        return UnknownNumberOfSigns()

    @v_args(inline=True)
    def ebl_atf_text_line__joiner(self, symbol):
        return Joiner(atf.Joiner(str(symbol)))

    @v_args(inline=True)
    def ebl_atf_text_line__in_word_newline(self, _):
        return InWordNewline()

    @v_args(inline=True)
    def ebl_atf_text_line__reading(self, name, sub_index, modifiers, flags, sign=None):
        return Reading.of(name.value, sub_index, modifiers, flags, sign)

    @v_args(inline=True)
    def ebl_atf_text_line__logogram(self, name, sub_index, modifiers, flags, sign=None):
        return Logogram.of(name.value, sub_index, modifiers, flags, sign)

    @v_args(inline=True)
    def ebl_atf_text_line__surrogate(
        self, name, sub_index, modifiers, flags, surrogate
    ):
        return Logogram.of(
            name.value, sub_index, modifiers, flags, None, surrogate.children
        )

    @v_args(inline=True)
    def ebl_atf_text_line__number(self, number, modifiers, flags, sign=None):
        return Number.of(number.value, modifiers, flags, sign)

    @v_args(inline=True)
    def ebl_atf_text_line__sub_index(self, sub_index=""):
        return sub_index_to_int(sub_index)

    def ebl_atf_text_line__modifiers(self, tokens):
        return tuple(map(str, tokens))

    def ebl_atf_text_line__flags(self, tokens):
        return tuple(map(atf.Flag, tokens))

    @v_args(inline=True)
    def ebl_atf_text_line__grapheme(self, name, modifiers, flags):
        return Grapheme.of(name.value, modifiers, flags)

    @v_args(inline=True)
    def ebl_atf_text_line__compound_grapheme(self, name):
        return CompoundGrapheme(name.value)


class TreeToWord(TreeToSign):
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

    def ebl_atf_text_line__lone_determinative(self, children):
        return self._create_word(LoneDeterminative, children)

    def ebl_atf_text_line__word(self, children):
        return self._create_word(Word, children)

    @staticmethod
    def _create_word(word_class: Type, children: Sequence):
        tokens = TreeToWord._children_to_tokens(children)

        value = "".join(token.value for token in tokens)
        return word_class(value, parts=tokens)

    @v_args(inline=True)
    def ebl_atf_text_line__unidentified_sign(self, flags):
        return UnidentifiedSign(flags)

    @v_args(inline=True)
    def ebl_atf_text_line__unclear_sign(self, flags):
        return UnclearSign(flags)

    @v_args(inline=True)
    def ebl_atf_text_line__unknown_number_of_signs(self, _):
        return UnknownNumberOfSigns()

    @v_args(inline=True)
    def ebl_atf_text_line__joiner(self, symbol):
        return Joiner(atf.Joiner(str(symbol)))

    @v_args(inline=True)
    def ebl_atf_text_line__in_word_newline(self, _):
        return InWordNewline()

    def ebl_atf_text_line__variant(self, children):
        tokens = self._children_to_tokens(children)
        return Variant(tuple(tokens))

    @v_args(inline=True)
    def ebl_atf_text_line__determinative(self, tree):
        tokens = self._children_to_tokens(tree.children)
        return Determinative(tokens)

    @v_args(inline=True)
    def ebl_atf_text_line__phonetic_gloss(self, tree):
        tokens = self._children_to_tokens(tree.children)
        return PhoneticGloss(tokens)

    @v_args(inline=True)
    def ebl_atf_text_line__linguistic_gloss(self, tree):
        tokens = self._children_to_tokens(tree.children)
        return LinguisticGloss(tokens)

    @v_args(inline=True)
    def ebl_atf_text_line__inline_erasure(self, erased, over_erased):
        return [
            Erasure.open(),
            *erased.children,
            Erasure.center(),
            *over_erased.children,
            Erasure.close(),
        ]

    @staticmethod
    def _children_to_tokens(children: Sequence) -> Sequence[Token]:
        return (
            pydash.chain(children)
            .flat_map_deep(
                lambda tree: (tree.children if isinstance(tree, Tree) else tree)
            )
            .map_(
                lambda token: (
                    ValueToken(token.value) if isinstance(token, Token) else token
                )
            )
            .value()
        )


class TreeToLine(TreeToWord):
    def empty_line(self, _):
        return EmptyLine()

    @v_args(inline=True)
    def control_line(self, prefix, content):
        return ControlLine.of_single(prefix, ValueToken(content))

    @v_args(inline=True)
    def text_line(self, prefix, content):
        return TextLine.of_iterable(LineNumberLabel.from_atf(prefix), content)

    def ebl_atf_text_line__text(self, children):
        return (
            pydash.chain(children)
            .flat_map_deep(
                lambda tree: (tree.children if isinstance(tree, Tree) else tree)
            )
            .map_(
                lambda token: (
                    ValueToken(str(token)) if isinstance(token, Token) else token
                )
            )
            .value()
        )

    @v_args(inline=True)
    def ebl_atf_text_line__broken_away(self, value):
        return BrokenAway(str(value))

    @v_args(inline=True)
    def ebl_atf_text_line__perhaps_broken_away(self, value):
        return PerhapsBrokenAway(str(value))

    @v_args(inline=True)
    def ebl_atf_text_line__cba(self, value):
        return BrokenAway(str(value))

    @v_args(inline=True)
    def ebl_atf_text_line__cpba(self, value):
        return PerhapsBrokenAway(str(value))

    @v_args(inline=True)
    def ebl_atf_text_line__oba(self, value):
        return BrokenAway(str(value))

    @v_args(inline=True)
    def ebl_atf_text_line__opba(self, value):
        return PerhapsBrokenAway(str(value))

    @v_args(inline=True)
    def ebl_atf_text_line__document_oriented_gloss(self, value):
        return DocumentOrientedGloss(str(value))

    @v_args(inline=True)
    def ebl_atf_text_line__odog(self, value):
        return DocumentOrientedGloss(str(value))

    @v_args(inline=True)
    def ebl_atf_text_line__cdog(self, value):
        return DocumentOrientedGloss(str(value))

    @v_args(inline=True)
    def ebl_atf_text_line__language_shift(self, value):
        return LanguageShift(str(value))

    def ebl_atf_text_line__line_continuation(self, _):
        return LineContinuation("→")

    @v_args(inline=True)
    def ebl_atf_text_line__tabulation(self, value):
        return Tabulation(value)

    @v_args(inline=True)
    def ebl_atf_text_line__commentary_protocol(self, value):
        return CommentaryProtocol(value)

    @v_args(inline=True)
    def ebl_atf_text_line__divider(self, value, modifiers, flags):
        return Divider.of(str(value), modifiers, flags)

    @v_args(inline=True)
    def ebl_atf_text_line__column(self, number):
        return Column(number and int(number))

    @v_args(inline=True)
    def ebl_atf_text_line__divider_variant(self, first, second):
        return Variant.of(
            ValueToken(str(first)) if isinstance(first, Token) else first,
            ValueToken(str(second)) if isinstance(second, Token) else second,
        )

    def ebl_atf_text_line__divider_variant_part(self, tokens):
        return self._create_word(Word, tokens)

    @v_args(inline=True)
    def ebl_atf_text_line__erasure(self, erased, over_erased):
        def set_erasure_state(tree: Tree, state: ErasureState):
            visitor = ErasureVisitor(state)
            for child in tree.children:
                visitor.visit(child)
            return visitor.tokens

        return [
            Erasure.open(),
            set_erasure_state(erased, ErasureState.ERASED),
            Erasure.center(),
            set_erasure_state(over_erased, ErasureState.OVER_ERASED),
            Erasure.close(),
        ]


class TreeDollarSignToTokens(TreeToLine):
    @v_args(inline=True)
    def ebl_atf_dollar_line__old(self, content):
        return ControlLine.of_single("$", ValueToken(content))

    @v_args(inline=True)
    def ebl_atf_dollar_line__loose(self, content):
        return LooseDollarLine(str(content)[1:-1])

    @v_args(inline=True)
    def ebl_atf_dollar_line__ruling(self, number, ruling):
        return RulingDollarLine(atf.Ruling(str(number)))

    @v_args(inline=True)
    def ebl_atf_dollar_line__image(self, number, letter, text):
        return ImageDollarLine(str(number), letter, str(text)[0:-1])

    @v_args(inline=True)
    def ebl_atf_dollar_line__STATUS(self, status):
        return atf.Status(str(status))

    @v_args(inline=True)
    def ebl_atf_dollar_line__STATE(self, state):
        return atf.State(str(state))

    @v_args(inline=True)
    def ebl_atf_dollar_line__OBJECT(self, object):
        return ScopeContainer(atf.Object(object))

    @v_args(inline=True)
    def ebl_atf_dollar_line__generic_object(self, object, text):
        return ScopeContainer(atf.Object(str(object)), str(text))

    @v_args(inline=True)
    def ebl_atf_dollar_line__SURFACE(self, surface):
        return ScopeContainer(atf.Surface.from_atf(str(surface)))

    @v_args(inline=True)
    def ebl_atf_dollar_line__generic_surface(self, surface, text):
        return ScopeContainer(atf.Surface.from_atf(str(surface)), str(text))

    @v_args(inline=True)
    def ebl_atf_dollar_line__EXTENT(self, extent):
        return atf.Extent(str(extent))

    @v_args(inline=True)
    def ebl_atf_dollar_line__NUMBER(self, number):
        return int(number)

    @v_args(inline=True)
    def ebl_atf_dollar_line__range(self, number1, number2):
        return (number1, number2)

    @v_args(inline=True)
    def ebl_atf_dollar_line__QUALIFICATION(self, qualification):
        return atf.Qualification(str(qualification))

    @v_args(inline=True)
    def ebl_atf_dollar_line__strict(
        self, qualification, extent, scope_container, state, status
    ):
        return StrictDollarLine(qualification, extent, scope_container, state, status)


WORD_PARSER = Lark.open("ebl_atf.lark", rel_to=__file__, start="any_word")
LINE_PARSER = Lark.open("ebl_atf.lark", rel_to=__file__)


def parse_word(atf):
    tree = WORD_PARSER.parse(atf)
    return TreeToWord().transform(tree)


def parse_erasure(atf):
    tree = LINE_PARSER.parse(atf, start="ebl_atf_text_line__erasure")
    return TreeToLine().transform(tree)


def parse_line(atf):
    tree = LINE_PARSER.parse(atf)
    return TreeDollarSignToTokens().transform(tree)


def parse_atf_lark(atf_):
    def parse_line_(line: str, line_number: int):
        try:
            return (parse_line(line), None) if line else (EmptyLine(), None)
        except UnexpectedInput as ex:
            description = "Invalid line: "
            context = ex.get_context(line, 6).split("\n", 1)
            return (
                None,
                {
                    "description": (
                        description
                        + context[0]
                        + "\n"
                        + len(description) * " "
                        + context[1]
                    ),
                    "lineNumber": line_number + 1,
                },
            )
        except ParseError as ex:
            return (
                None,
                {"description": f"Invalid line: {ex}", "lineNumber": line_number + 1,},
            )

    def check_errors(pairs):
        errors = [error for line, error in pairs if error is not None]
        if any(errors):
            raise TransliterationError(errors)

    lines = tuple(
        pydash.chain(atf_)
        .split("\n")
        .map(parse_line_)
        .tap(check_errors)
        .map(lambda pair: pair[0])
        .drop_right_while(lambda line: line.prefix == "")
        .value()
    )

    return Text(lines, f"{atf.ATF_PARSER_VERSION}")
