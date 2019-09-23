import attr
import pydash
from lark.exceptions import UnexpectedInput
from lark.lark import Lark
from lark.lexer import Token
from lark.tree import Tree
from lark.visitors import Transformer, v_args

from ebl.atf.atf import ATF_PARSER_VERSION
from ebl.transliteration.labels import LineNumberLabel
from ebl.transliteration.line import ControlLine, EmptyLine, TextLine
from ebl.transliteration.text import Text
from ebl.transliteration.token import BrokenAway, DocumentOrientedGloss, \
    Erasure, \
    ErasureState, LanguageShift, LineContinuation, LoneDeterminative, \
    OmissionOrRemoval, Partial, PerhapsBrokenAway, Side, Token as EblToken, \
    Word
from ebl.transliteration.transliteration_error import TransliterationError


class TreeToWord(Transformer):
    def lone_determinative(self, tokens):
        return LoneDeterminative(''.join(
            token.value for token in tokens
        ))

    def word(self, tokens):
        return Word(''.join(
            token.value for token in tokens
        ))

    def left_partial_word(self, tokens):
        return Word(''.join(
            token.value for token in tokens
        ))

    def right_partial_word(self, tokens):
        return Word(''.join(
            token.value for token in tokens
        ))

    def partial_word(self, tokens):
        return Word(''.join(
            token.value for token in tokens
        ))


class TreeToErasure(TreeToWord):
    def erasure(self, tokens):
        def set_state(children, state):
            # TODO: Move to Token
            return [
                (attr.evolve(child, erasure=state)
                 if isinstance(child, Word)
                 else child)
                for child in children
            ]
        [erased, over_erased] = tokens
        return [Erasure('°', Side.LEFT),
                set_state(erased.children, ErasureState.ERASED),
                Erasure('\\', Side.CENTER),
                set_state(over_erased.children, ErasureState.OVER_ERASED),
                Erasure('°', Side.RIGHT)]


class TreeToLine(TreeToErasure):
    def empty_line(self, _):
        return EmptyLine()

    @v_args(inline=True)
    def control_line(self, prefix, content):
        return ControlLine.of_single(prefix, EblToken(content))

    @v_args(inline=True)
    def text_line(self, prefix, content):
        return TextLine.of_iterable(LineNumberLabel.from_atf(prefix), content)

    def text(self, children):
        return (pydash
                .chain(children)
                .flat_map_deep(lambda tree: (tree.children
                                             if isinstance(tree, Tree)
                                             else tree))
                .map_(lambda token: (EblToken(str(token))
                                     if isinstance(token, Token)
                                     else token))
                .value())

    @v_args(inline=True)
    def broken_away(self, value):
        return BrokenAway(str(value))

    @v_args(inline=True)
    def perhaps_broken_away(self, value):
        return PerhapsBrokenAway(str(value))

    @v_args(inline=True)
    def cba(self, value):
        return BrokenAway(str(value))

    @v_args(inline=True)
    def cpba(self, value):
        return PerhapsBrokenAway(str(value))

    @v_args(inline=True)
    def oba(self, value):
        return BrokenAway(str(value))

    @v_args(inline=True)
    def opba(self, value):
        return PerhapsBrokenAway(str(value))

    @v_args(inline=True)
    def omission_or_removal(self, value):
        return OmissionOrRemoval(str(value))

    @v_args(inline=True)
    def oo(self, value):
        return OmissionOrRemoval(str(value))

    @v_args(inline=True)
    def co(self, value):
        return OmissionOrRemoval(str(value))

    @v_args(inline=True)
    def document_oriented_gloss(self, value):
        return DocumentOrientedGloss(str(value))

    @v_args(inline=True)
    def odog(self, value):
        return DocumentOrientedGloss(str(value))

    @v_args(inline=True)
    def cdog(self, value):
        return DocumentOrientedGloss(str(value))

    @v_args(inline=True)
    def language_shift(self, value):
        return LanguageShift(str(value))

    @v_args(inline=True)
    def unknown_number_of_signs(self, value):
        return EblToken(str(value))

    @v_args(inline=True)
    def lone_determinative_complex(self, prefix, lone_determinative, suffix):
        return pydash.flatten([
            prefix.children,
            LoneDeterminative.of_value(
                lone_determinative.value,
                Partial(start=len(prefix.children) > 0,
                        end=len(suffix.children) > 0)),
            suffix.children
        ])

    def line_continuation(self, _):
        return LineContinuation('→')


WORD_PARSER = Lark.open('ebl-atf.lark', rel_to=__file__, start='any_word')
LINE_PARSER = Lark.open('ebl-atf.lark', rel_to=__file__)


def parse_word(atf):
    tree = WORD_PARSER.parse(atf)
    return TreeToWord().transform(tree)


def parse_erasure(atf):
    tree = LINE_PARSER.parse(atf, start='erasure')
    return TreeToErasure().transform(tree)


def parse_line(atf):
    tree = LINE_PARSER.parse(atf)
    return TreeToLine().transform(tree)


def parse_atf_lark(atf):
    def parse_line_(line: str, line_number: int):
        try:
            return ((parse_line(line), None)
                    if line else
                    (EmptyLine(), None))
        except UnexpectedInput as ex:
            return (None,  {
                'description': 'Invalid line: ' + ex.get_context(line, 6),
                'lineNumber': line_number + 1
            })

    def check_errors(pairs):
        errors = [
            error
            for line, error in pairs
            if error is not None
        ]
        if any(errors):
            raise TransliterationError(errors)

    lines = tuple(pydash
                  .chain(atf)
                  .split('\n')
                  .map(parse_line_)
                  .tap(check_errors)
                  .map(lambda pair: pair[0])
                  .drop_right_while(lambda line: line.prefix == '')
                  .value())

    return Text(lines, f'{ATF_PARSER_VERSION}-lark')
