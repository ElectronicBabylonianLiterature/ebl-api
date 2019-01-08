import re
import pydash
from parsy import string, regex, seq, ParseError, char_from, string_from
from ebl.text.atf import AtfSyntaxError
from ebl.text.line import EmptyLine, TextLine, ControlLine
from ebl.text.text import Text
from ebl.text.token import Token, Word, LanguageShift


def variant(parser):
    variant_separator = string('/').desc('variant separator')
    return parser + (variant_separator + parser).many().concat()

FLAG = char_from('!?*#').many().concat().desc('flag')
OMISSION = string_from(
    '<<', '<(', '<', '>>', ')>', '>'
).desc('omission or removal')
GLOSS = string_from('{{', '}}')
DETERMINATIVE = (
    string_from('{+', '{') |
    string('}') + FLAG
)
JOINER = (
    OMISSION |
    GLOSS |
    DETERMINATIVE |
    string_from('-', '{{', '{+', '{', '+', '}}', '}') |
    regex(r'(?<!\.)\.(?!\.)')
).desc('joiner')
WORD_SEPARATOR = string(' ').desc('word separtor')
LINE_SEPARATOR = regex(r'\n').desc('line separator')
WORD_SEPARATOR_OR_EOL = WORD_SEPARATOR | regex(r'(?=\n|$)')
LINE_NUMBER = regex(r'[^.\s]+\.').at_least(1).concat().desc('line number')
TABULATION = string('($___$)').desc('tabulation')
COLUMN = regex(r'&\d*').desc('column') << WORD_SEPARATOR_OR_EOL
DIVIDER = (
    string_from(
        '|', ':\'', ':"', ':.', '::', ':?', ':', ';', '/'
    ) +
    FLAG
).desc('divider') << WORD_SEPARATOR_OR_EOL
COMMENTARY_PROTOCOL = regex(r'!(qt|bs|cm|zz)').desc('commentary protocol')
LACUNA = regex(r'\[?\.\.\.\]?').desc('lacuna')
SHIFT = regex(r'%\w+').desc('language or register/writing system shift')
UNKNOWN = (
    char_from('Xx') +
    FLAG
).desc('unclear or unindentified')
SUB_INDEX = regex(r'[₀-₉ₓ]+').desc('subindex')
VALUE = seq(
    regex(r"[aāâbdeēêghiīîyklmnpqrsṣštṭuūûwzḫʾ0-9\[\]()]+"),
    SUB_INDEX.optional(),
    FLAG
).map(pydash.compact).concat().desc('reading')
GRAPHEME = (
    regex(r'\$?[A-ZṢŠṬa-zṣšṭ0-9₀-₉\[\]]+') +
    FLAG
).desc('grapheme')
COMPOUND_GRAPHEME_OPERATOR = char_from('.×%&+()').desc(
    'compound grapheme operator'
)
COMPUND_PART = variant(GRAPHEME)
COMPOUND_GRAPHEME = (
    seq(
        string('|').optional(),
        COMPUND_PART,
        (
            COMPOUND_GRAPHEME_OPERATOR.many().concat() +
            COMPUND_PART
        ).many().concat(),
        string('|').optional()
    )
    .map(pydash.flatten_deep)
    .map(pydash.compact)
    .concat()
    .desc('compound grapheme')
)
VALUE_WITH_SIGN = VALUE + regex(r'!?\(') + COMPOUND_GRAPHEME + string(')')
VARIANT = variant(
    UNKNOWN |
    VALUE_WITH_SIGN |
    VALUE |
    COMPOUND_GRAPHEME |
    GRAPHEME |
    DIVIDER
)
WORD = seq(
    JOINER.many().concat(),
    VARIANT,
    (JOINER.many().concat() + VARIANT).many(),
    JOINER.many().concat(),
    FLAG
).map(
    pydash.flatten_deep
).map(
    pydash.compact
).map(
    ''.join
).desc('word')


CONTROL_LINE = seq(
    regex(r'(=:|\$|@|&|#)'),
    regex(r'.*').map(Token)
).combine(ControlLine.of_single)
EMPTY_LINE = regex(
    r'^$', re.RegexFlag.MULTILINE
).map(lambda _: EmptyLine()) << LINE_SEPARATOR
TEXT_LINE = seq(
    LINE_NUMBER << WORD_SEPARATOR,
    (
        TABULATION.map(Token) |
        COLUMN.map(Token) |
        DIVIDER.map(Token) |
        COMMENTARY_PROTOCOL.map(Token) |
        LACUNA.map(Token) |
        SHIFT.map(LanguageShift) |
        WORD.map(Word) |
        OMISSION.map(Token)
    ).many().sep_by(WORD_SEPARATOR).map(pydash.flatten)
).combine(TextLine.of_iterable)


ATF = (
    (CONTROL_LINE | TEXT_LINE | EMPTY_LINE)
    .many()
    .sep_by(LINE_SEPARATOR)
    .map(pydash.flatten)
    .map(tuple)
    .map(Text)
)


def parse_atf(atf: str):
    try:
        return ATF.parse(atf)
    except ParseError as error:
        line_number = int(error.line_info().split(':')[0]) + 1
        raise AtfSyntaxError(line_number)
