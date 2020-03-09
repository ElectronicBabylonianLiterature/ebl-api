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
from ebl.transliteration.domain.dollar_line import (
    ImageDollarLine,
    LooseDollarLine,
    RulingDollarLine,
    ScopeContainer,
    StateDollarLine,
)
from ebl.transliteration.domain.enclosure_error import EnclosureError
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
from ebl.transliteration.domain.enclosure_visitor import EnclosureVisitor
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.line import (
    ControlLine,
    EmptyLine,
    Line,
    TextLine,
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
        return UnidentifiedSign.of(flags)

    @v_args(inline=True)
    def ebl_atf_text_line__unclear_sign(self, flags):
        return UnclearSign.of(flags)

    @v_args(inline=True)
    def ebl_atf_text_line__unknown_number_of_signs(self, _):
        return UnknownNumberOfSigns(frozenset())

    @v_args(inline=True)
    def ebl_atf_text_line__joiner(self, symbol):
        return Joiner(atf.Joiner(str(symbol)))

    @v_args(inline=True)
    def ebl_atf_text_line__in_word_newline(self, _):
        return InWordNewline()

    @v_args(inline=True)
    def ebl_atf_text_line__reading(self, name, sub_index, modifiers, flags, sign=None):
        return Reading.of(tuple(name.children), sub_index, modifiers, flags, sign)

    @v_args()
    def ebl_atf_text_line__value_name_part(self, children):
        return ValueToken.of("".join(children))

    @v_args(inline=True)
    def ebl_atf_text_line__logogram(self, name, sub_index, modifiers, flags, sign=None):
        return Logogram.of(tuple(name.children), sub_index, modifiers, flags, sign)

    @v_args(inline=True)
    def ebl_atf_text_line__surrogate(
        self, name, sub_index, modifiers, flags, surrogate
    ):
        return Logogram.of(
            tuple(name.children), sub_index, modifiers, flags, None, surrogate.children
        )

    @v_args()
    def ebl_atf_text_line__logogram_name_part(self, children):
        return ValueToken.of("".join(children))

    @v_args(inline=True)
    def ebl_atf_text_line__number(self, number, modifiers, flags, sign=None):
        return Number.of(tuple(number.children), modifiers, flags, sign)

    @v_args()
    def ebl_atf_text_line__number_name_head(self, children):
        return ValueToken.of("".join(children))

    @v_args()
    def ebl_atf_text_line__number_name_part(self, children):
        return ValueToken.of("".join(children))

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
        return CompoundGrapheme.of(name.value)

    def ebl_atf_text_line__close_broken_away(self, _):
        return BrokenAway.close()

    def ebl_atf_text_line__open_broken_away(self, _):
        return BrokenAway.open()


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
        return word_class.of(tokens)

    @v_args(inline=True)
    def ebl_atf_text_line__joiner(self, symbol):
        return Joiner(frozenset(), atf.Joiner(str(symbol)))

    @v_args(inline=True)
    def ebl_atf_text_line__in_word_newline(self, _):
        return InWordNewline(frozenset())

    def ebl_atf_text_line__variant(self, children):
        tokens = self._children_to_tokens(children)
        return Variant.of(*tokens)

    @v_args(inline=True)
    def ebl_atf_text_line__determinative(self, tree):
        tokens = self._children_to_tokens(tree.children)
        return Determinative.of(tokens)

    @v_args(inline=True)
    def ebl_atf_text_line__phonetic_gloss(self, tree):
        tokens = self._children_to_tokens(tree.children)
        return PhoneticGloss.of(tokens)

    @v_args(inline=True)
    def ebl_atf_text_line__linguistic_gloss(self, tree):
        tokens = self._children_to_tokens(tree.children)
        return LinguisticGloss.of(tokens)

    @v_args(inline=True)
    def ebl_atf_text_line__inline_erasure(self, erased, over_erased):
        return [
            Erasure.open(),
            *erased.children,
            Erasure.center(),
            *over_erased.children,
            Erasure.close(),
        ]

    def ebl_atf_text_line__close_perhaps_broken_away(self, _):
        return PerhapsBrokenAway.close()

    def ebl_atf_text_line__open_perhaps_broken_away(self, _):
        return PerhapsBrokenAway.open()

    @staticmethod
    def _children_to_tokens(children: Sequence) -> Sequence[Token]:
        return (
            pydash.chain(children)
            .flat_map_deep(
                lambda tree: (tree.children if isinstance(tree, Tree) else tree)
            )
            .map_(
                lambda token: (
                    ValueToken.of(token.value) if isinstance(token, Token) else token
                )
            )
            .value()
        )


class TreeToLine(TreeToWord):
    def empty_line(self, _):
        return EmptyLine()

    @v_args(inline=True)
    def control_line(self, prefix, content):
        return ControlLine.of_single(prefix, ValueToken.of(content))

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
                    ValueToken.of(str(token)) if isinstance(token, Token) else token
                )
            )
            .value()
        )

    @v_args(inline=True)
    def ebl_atf_text_line__open_document_oriented_gloss(self, _):
        return DocumentOrientedGloss.open()

    @v_args(inline=True)
    def ebl_atf_text_line__close_document_oriented_gloss(self, _):
        return DocumentOrientedGloss.close()

    @v_args(inline=True)
    def ebl_atf_text_line__language_shift(self, value):
        return LanguageShift.of(str(value))

    def ebl_atf_text_line__line_continuation(self, _):
        return LineContinuation.of("→")

    @v_args(inline=True)
    def ebl_atf_text_line__tabulation(self, value):
        return Tabulation.of(value)

    @v_args(inline=True)
    def ebl_atf_text_line__commentary_protocol(self, value):
        return CommentaryProtocol.of(value)

    @v_args(inline=True)
    def ebl_atf_text_line__divider(self, value, modifiers, flags):
        return Divider.of(str(value), modifiers, flags)

    @v_args(inline=True)
    def ebl_atf_text_line__column(self, number):
        return Column.of(number and int(number))

    @v_args(inline=True)
    def ebl_atf_text_line__divider_variant(self, first, second):
        return Variant.of(first, second)

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
    def ebl_atf_dollar_line__free_text(self, content):
        return "".join(content)

    @v_args(inline=True)
    def ebl_atf_dollar_line__loose(self, content):
        return LooseDollarLine(str(content))

    @v_args(inline=True)
    def ebl_atf_dollar_line__ruling(self, number, status=None):
        return RulingDollarLine(atf.Ruling(str(number)), status)

    @v_args(inline=True)
    def ebl_atf_dollar_line__image(self, number, letter, text):
        return ImageDollarLine(str(number), letter and str(letter), text)

    @v_args(inline=True)
    def ebl_atf_dollar_line__DOLLAR_STATUS(self, status):
        return atf.DollarStatus(str(status))

    @v_args(inline=True)
    def ebl_atf_dollar_line__STATE(self, state):
        return atf.State(str(state))

    @v_args(inline=True)
    def ebl_atf_dollar_line__OBJECT(self, object):
        return ScopeContainer(atf.Object(object))

    @v_args(inline=True)
    def ebl_atf_dollar_line__generic_object(self, text):
        return ScopeContainer(atf.Object.OBJECT, str(text))

    @v_args(inline=True)
    def ebl_atf_dollar_line__fragment(self, text):
        return ScopeContainer(atf.Object.FRAGMENT, str(text))

    @v_args(inline=True)
    def ebl_atf_dollar_line__SURFACE(self, surface):
        return ScopeContainer(atf.Surface.from_atf(str(surface)))

    @v_args(inline=True)
    def ebl_atf_dollar_line__generic_surface(self, text):
        return ScopeContainer(atf.Surface.SURFACE, str(text))

    @v_args(inline=True)
    def ebl_atf_dollar_line__face(self, text):
        return ScopeContainer(atf.Surface.FACE, str(text))

    @v_args(inline=True)
    def ebl_atf_dollar_line__edge(self, text=""):
        return ScopeContainer(atf.Surface.EDGE, str(text))

    @v_args(inline=True)
    def ebl_atf_dollar_line__SCOPE(self, scope):
        return ScopeContainer(atf.Scope(str(scope)))

    @v_args(inline=True)
    def ebl_atf_dollar_line__EXTENT(self, extent):
        return atf.Extent(str(extent))

    @v_args(inline=True)
    def ebl_atf_dollar_line__INT(self, number):
        return int(number)

    @v_args(inline=True)
    def ebl_atf_dollar_line__range(self, number1, number2):
        return (number1, number2)

    @v_args(inline=True)
    def ebl_atf_dollar_line__QUALIFICATION(self, qualification):
        return atf.Qualification(str(qualification))

    @v_args(inline=True)
    def ebl_atf_dollar_line__state(
        self, qualification, extent=None, scope_container=None, state=None, status=None
    ):
        return StateDollarLine(qualification, extent, scope_container, state, status)

    @v_args(inline=True)
    def ebl_atf_dollar_line__state_extent(
        self, extent, scope_container=None, state=None, status=None
    ):
        return StateDollarLine(None, extent, scope_container, state, status)

    @v_args(inline=True)
    def ebl_atf_dollar_line__state_scope(
        self, scope_container, state=None, status=None
    ):
        return StateDollarLine(None, None, scope_container, state, status)

    @v_args(inline=True)
    def ebl_atf_dollar_line__state_state(self, state, status):
        return StateDollarLine(None, None, None, state, status)

    @v_args(inline=True)
    def ebl_atf_dollar_line__state_status(self, status):
        return StateDollarLine(None, None, None, None, status)


WORD_PARSER = Lark.open(
    "ebl_atf.lark", maybe_placeholders=True, rel_to=__file__, start="any_word"
)
LINE_PARSER = Lark.open("ebl_atf.lark", maybe_placeholders=True, rel_to=__file__)


def parse_word(atf: str) -> Word:
    tree = WORD_PARSER.parse(atf)
    return TreeToWord().transform(tree)


def parse_erasure(atf: str) -> Sequence[EblToken]:
    tree = LINE_PARSER.parse(atf, start="ebl_atf_text_line__erasure")
    return TreeToLine().transform(tree)


def parse_line(atf: str) -> Line:
    tree = LINE_PARSER.parse(atf)
    return TreeDollarSignToTokens().transform(tree)


def validate_line(line: Line) -> None:
    visitor = EnclosureVisitor()
    for token in line.content:
        token.accept(visitor)
    visitor.done()


def parse_atf_lark(atf_):
    def parse_line_(line: str, line_number: int):
        try:
            parsed_line = parse_line(line) if line else EmptyLine()
            validate_line(parsed_line)
            return parsed_line, None
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
        except EnclosureError:
            return (
                None,
                {"description": f"Invalid brackets.", "lineNumber": line_number + 1,},
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
