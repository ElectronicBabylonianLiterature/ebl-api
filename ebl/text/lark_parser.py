from lark.lark import Lark
from lark.visitors import Transformer

from ebl.text.token import LoneDeterminative, Word

GRAMMAR = r'''
?start: lone_determinative | word

DIVIDER: INLINE_BROKEN_AWAY? DIVIDER_SYMBOL MODIFIER FLAG INLINE_BROKEN_AWAY?
DIVIDER_SYMBOL: "|" | ":'" | ":\"" | ":." | "::" | ":?" | ":" | ";" | "/"

OMISSION: OPEN_OMISSION
        | CLOSE_OMISSION
OPEN_OMISSION: "<<" | "<(" | "<"
CLOSE_OMISSION: ">>" | ")>" | ">"

BROKEN_AWAY: OPEN_BROKEN_AWAY
           | CLOSE_BROKEN_AWAY
OPEN_BROKEN_AWAY: "["
CLOSE_BROKEN_AWAY: "]"

INLINE_BROKEN_AWAY: OPEN_INLINE_BROKEN_AWAY 
                  | CLOSE_INLINE_BROKEN_AWAY
OPEN_INLINE_BROKEN_AWAY: /(\[\(|\[|(?<!{)\()(?!\.)/
CLOSE_INLINE_BROKEN_AWAY: /(?<!\.)(\)\]|\)(?!})|\])/

lone_determinative: LD_PREFIX VARIANT (JOINER* VARIANT)* LD_SUFFIX
LD_PREFIX: OMISSION? OPEN_DETERMINATIVE OPEN_BROKEN_AWAY?
LD_SUFFIX: CLOSE_BROKEN_AWAY? CLOSE_DETERMINATIVE OMISSION?

word:  WORD_PREFIX? OPEN_OMISSION? WORD_BODY CLOSE_OMISSION? WORD_SUFFIX?
WORD_PREFIX: JOINER+ OPEN_INLINE_BROKEN_AWAY?
WORD_BODY: (INLINE_ERASURE (PART_JOINER (INLINE_ERASURE | PARTS))* | PARTS)
WORD_SUFFIX: CLOSE_INLINE_BROKEN_AWAY? JOINER+

INLINE_ERASURE: "°" PARTS "\\" PARTS "°"

PARTS: DETERMINATIVE (PART_JOINER? (DETERMINATIVE | VARIANT))+
     | VARIANT (PART_JOINER? (DETERMINATIVE | VARIANT))*

DETERMINATIVE: D_PREFIX VARIANT (PART_JOINER VARIANT)* D_SUFFIX
D_PREFIX: OMISSION? OPEN_DETERMINATIVE OPEN_BROKEN_AWAY?
D_SUFFIX: CLOSE_BROKEN_AWAY? CLOSE_DETERMINATIVE OMISSION?
OPEN_DETERMINATIVE: "{+" | "{"
CLOSE_DETERMINATIVE: "}"

PART_JOINER: ANY_CLOSE? JOINER+ ANY_OPEN?
           | ANY_CLOSE JOINER* ANY_OPEN?
           | ANY_CLOSE? JOINER* ANY_OPEN
ANY_CLOSE: CLOSE_INLINE_BROKEN_AWAY CLOSE_OMISSION?
         | CLOSE_INLINE_BROKEN_AWAY? CLOSE_OMISSION
ANY_OPEN: OPEN_OMISSION OPEN_INLINE_BROKEN_AWAY?
        | OPEN_OMISSION? OPEN_INLINE_BROKEN_AWAY
JOINER: LINGUISTIC_GLOSS | "-" | "+" | "."
LINGUISTIC_GLOSS: "{{" 
                | "}}"

VARIANT: VARIANT_PART (VARIANT_SEPARATOR VARIANT_PART)*
VARIANT_PART: UNKNOWN
            | VALUE_WITH_SIGN
            | VALUE 
            | COMPOUND_GRAPHEME 
            | GRAPHEME
            | DIVIDER
 
VALUE_WITH_SIGN: VALUE "!"? "(" COMPOUND_GRAPHEME ")"

VALUE: VALUE_NAME SUB_INDEX? MODIFIER FLAG
VALUE_NAME:  VALUE_CHARACTER (INLINE_BROKEN_AWAY? VALUE_CHARACTER)*
VALUE_CHARACTER: "a" | "ā" | "â" | "b" | "d" | "e" | "ē" | "ê" | "g" | "h" 
               | "i" | "ī" | "î" | "y" | "k" | "l" | "m" | "n" | "p" | "q"
               | "r" | "s" | "ṣ" | "š" | "t" | "ṭ" | "u" | "ū" | "û" | "w"
               | "z" | "ḫ" | "ʾ" | "0".."9"
SUB_INDEX: ("₀".."₉" | "ₓ")+

COMPOUND_GRAPHEME: "|"? COMPOUND_PART (COMPOUND_OPERATOR COMPOUND_PART)* "|"?
COMPOUND_PART: GRAPHEME (VARIANT_SEPARATOR GRAPHEME)*
COMPOUND_OPERATOR: "." | "×" | "%" | "&" | "+" | "(" | ")"

GRAPHEME: "$"?  GRAPHEME_NAME MODIFIER FLAG
GRAPHEME_NAME: GRAPHEME_CHARACTER (INLINE_BROKEN_AWAY? GRAPHEME_CHARACTER)*
GRAPHEME_CHARACTER: "a".."z"
                  | "A".."Z"
                  | "Ṣ" | "Š" | "Ṭ"
                  | "ṣ" | "š" | "ṭ"
                  | "0".."9"
                  | "₀".."₉"

UNKNOWN: ("X" | "x") FLAG

VARIANT_SEPARATOR: "/"

FLAG: ("!" | "?" | "*" | "#")*
MODIFIER: ("@" (MODIFIER_CHARACTER | ("0".."9")+))*
MODIFIER_CHARACTER: "c" | "f" | "g" | "s" | "t" | "n" | "z" | "k" | "r" | "h"
                  | "v"
'''


class TreeToWord(Transformer):

    def lone_determinative(self, tokens):
        return LoneDeterminative(''.join(
            token.value for token in tokens
        ))

    def word(self, tokens):
        return Word(''.join(
            token.value for token in tokens
        ))


PARSER = Lark(GRAMMAR)


def parse_word(atf):
    tree = PARSER.parse(atf)
    return TreeToWord().transform(tree)
