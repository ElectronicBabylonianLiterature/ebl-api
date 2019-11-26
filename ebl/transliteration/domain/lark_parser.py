import attr
import pydash
from lark.exceptions import UnexpectedInput, ParseError
from lark.lark import Lark
from lark.lexer import Token
from lark.tree import Tree
from lark.visitors import Transformer, v_args

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.atf import sub_index_to_int
from ebl.transliteration.domain.enclosure_tokens import Side, \
    DocumentOrientedGloss, BrokenAway, PerhapsBrokenAway, Erasure, \
    OmissionOrRemoval
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.line import ControlLine, EmptyLine, TextLine
from ebl.transliteration.domain.sign_tokens import Divider, UnidentifiedSign, \
    UnclearSign, Reading, Number
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.tokens import LanguageShift, \
    LineContinuation, ValueToken, UnknownNumberOfSigns, Tabulation, \
    CommentaryProtocol, Column, Variant
from ebl.transliteration.domain.transliteration_error import \
    TransliterationError
from ebl.transliteration.domain.word_tokens import ErasureState, Word, \
    LoneDeterminative, Joiner, InWordNewline


class TreeToWord(Transformer):
    def lone_determinative(self, children):
        return self._create_word(LoneDeterminative, children)

    def word(self, children):
        return self._create_word(Word, children)

    @staticmethod
    def _create_word(word_class, children):
        tokens = (pydash
                  .chain(children)
                  .flat_map_deep(lambda tree: (tree.children
                                               if isinstance(tree, Tree)
                                               else tree))
                  .map_(lambda token: (ValueToken(str(token))
                                       if isinstance(token, Token)
                                       else token))
                  .value())

        value = ''.join(token.value for token in tokens)
        return word_class(value, parts=tokens)

    @v_args(inline=True)
    def unidentified_sign(self, flags):
        return UnidentifiedSign(flags)

    @v_args(inline=True)
    def unclear_sign(self, flags):
        return UnclearSign(flags)

    @v_args(inline=True)
    def unknown_number_of_signs(self, _):
        return UnknownNumberOfSigns()

    @v_args(inline=True)
    def joiner(self, symbol):
        return Joiner(atf.Joiner(str(symbol)))

    @v_args(inline=True)
    def in_word_newline(self, _):
        return InWordNewline()

    @v_args(inline=True)
    def reading(self, name, sub_index, modifiers, flags, sign=None):
        return Reading.of(name.value,
                          sub_index,
                          modifiers,
                          flags,
                          sign)

    @v_args(inline=True)
    def number(self, number, modifiers, flags, sign=None):
        return Number.of(int(number),
                         modifiers,
                         flags,
                         sign)

    @v_args(inline=True)
    def sub_index(self, sub_index=''):
        return sub_index_to_int(sub_index)

    def modifiers(self, tokens):
        return tuple(map(str, tokens))

    def flags(self, tokens):
        return tuple(map(atf.Flag, tokens))


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
        return ControlLine.of_single(prefix, ValueToken(content))

    @v_args(inline=True)
    def text_line(self, prefix, content):
        return TextLine.of_iterable(LineNumberLabel.from_atf(prefix), content)

    def text(self, children):
        return (pydash
                .chain(children)
                .flat_map_deep(lambda tree: (tree.children
                                             if isinstance(tree, Tree)
                                             else tree))
                .map_(lambda token: (ValueToken(str(token))
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

    def line_continuation(self, _):
        return LineContinuation('→')

    @v_args(inline=True)
    def tabulation(self, value):
        return Tabulation(value)

    @v_args(inline=True)
    def commentary_protocol(self, value):
        return CommentaryProtocol(value)

    @v_args(inline=True)
    def divider(self, value, modifiers, flags):
        return Divider(str(value), modifiers, flags)

    @v_args(inline=True)
    def column(self, number):
        children = number.children
        return Column(int(''.join(children)) if children else None)

    @v_args(inline=True)
    def divider_variant(self, first, second):
        return Variant.of(first, second)

    def variant_part(self, tokens):
        return self._create_word(Word, tokens)


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


def parse_atf_lark(atf_):
    def parse_line_(line: str, line_number: int):
        try:
            return ((parse_line(line), None)
                    if line else
                    (EmptyLine(), None))
        except UnexpectedInput as ex:
            description = 'Invalid line: '
            context = ex.get_context(line, 6).split('\n', 1)
            return (None,  {
                'description': (description + context[0] + '\n' +
                                len(description)*' ' + context[1]),
                'lineNumber': line_number + 1
            })
        except ParseError as ex:
            return (None,  {
                'description': f'Invalid line: {ex}',
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
                  .chain(atf_)
                  .split('\n')
                  .map(parse_line_)
                  .tap(check_errors)
                  .map(lambda pair: pair[0])
                  .drop_right_while(lambda line: line.prefix == '')
                  .value())

    return Text(lines, f'{atf.ATF_PARSER_VERSION}')
