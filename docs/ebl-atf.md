eBL-ATF is based on [Oracc-ATF](http://oracc.museum.upenn.edu/doc/help/editinginatf/index.html)
but is not fully compatible with other ATF flavours. eBL-ATF uses UTF-8
encoding. The grammar definitions below use [EBNF](https://en.wikipedia.org/wiki/Extended_Backus–Naur_form)
([ISO/IEC 14977 : 1996(E)](https://standards.iso.org/ittf/PubliclyAvailableStandards/s026153_ISO_IEC_14977_1996(E).zip)).

The EBNF grammar below is an idealized representation of the eBL-ATF as it does
not deal with ambiguities and implentattional details necessary to create the
domain model in practice. A fully functional grammar is defined in
[ebl-atf.lark](https://github.com/ElectronicBabylonianLiterature/ebl-api/blob/master/ebl/text/ebl-atf.lark).
The file uses the EBNF variant of the [Lark parsing library](https://github.com/lark-parser/lark).
See [Grammar Reference](https://lark-parser.readthedocs.io/en/latest/grammar/)
and [Lark Cheat Sheet](https://lark-parser.readthedocs.io/en/latest/lark_cheatsheet.pdf).


eBL-ATF can be empty or consist of lines separated by a newline character.

```ebnf
ebl-atf = [ line, { eol, line } ];

free-text = { any-character }+;
word-character = ? A-Za-z ?;
lower-case-letter = ? a-z ?;
any-character = ? any UTF-8 character ?;
decimal-digit = '0' | '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9';
eol = ? end of line ?;
```

## Lines

A line can be either *empty*, *control* or *text line*. Text lines contain
transliterated text. Other lines do not currently have special semantics.
Continuation lines (starting with space) are not supported.

```ebnf
line = empty-line
     | dollar-line
     | control-line
     | text-line;

empty-line = '';

control-line = '=:' | '&' | '#', { any-character };

text-line = line-number, ' ', text;
line-number = { not-space }-, '.';
not-space = any-character - ' ';
```
## @-lines


@-lines are used for structural tags. Several kinds of structure may be indicated 
using this mechanism: physical structure, e.g., objects, surfaces; manuscript structure,
i.e., columns; and document structure, e.g., divisions and colophons.

```ebnf

at-line = seal | column | heading | discourse | objct_with_status | surface_with_status
          | divisions | composite
    
surface_with_status = _surface, " "?, status*
//_surface same as surface in $-line
//status same as status from Labels

object_with_status = _object, " "?, status*
//_object same as surface in $-line
    
column = "column ", number, " "?, status*

heading: "h",number

discourse = "catchline" | "colophon" | "date" | "signature" | "signatures" 
            | "summary"  | "witnesses"

divisions = "m=division ", free-text, [" ", number]

composite = composite_start | composite_end
composite_start = "div ", free-text, [" ", number]
composite_end = "end ", free-text

number = { decimal-digit }-;


## $-lines

$-lines are used to indicate information about the state of the text or object,
or to describe features on the object which are not part of the transliteration
proper.

- State: `$ <qualification> <extent> <scope> <state> <status>`, e.g.: 
  `$ 3 lines blank` or `$ rest of obverse missing`.
- Loose: `$ (<free text>)`, e.g.: `$ (head of statue broken)`
- Ruling: `$ (single | double | triple) ruling`, e.g.: `$ double ruling`.
- Image: `$ (image N = <free text>)`, e.g.:
  `$ (image 1 = numbered diagram of triangle)`

```ebnf
dollar-line = '$', [ ' ' ], ( strict | '(', strict, ')' | loose );
strict = state | ruling | image

state = [ qualification ], [' ', extend ], [' ', scope ], [ ' ', state-name ],
        [ ' ', dollar-status ]; (* At least one column is required. *)

qualification = 'at least' | 'at most' | 'about';

extent = 'several' | 'some' | number | range | 'rest of' | 'start of'
       | beginning of | 'middle of' | 'end of';
    
scope = object | surface | 'column' | 'columns' | 'line' | 'lines' | 'case'
      | 'cases' | 'side' | 'excerpt' | 'surface';

state-name = 'blank' | 'broken' | 'effaced' | 'illegible' | 'missing'
            | 'traces' | 'omitted' | 'continues';

dollar-status = '*' | '?' | '!' | '!?';

range = number, '-', number;

object = 'tablet' | 'envelope' | 'prism' | 'bulla' | fragment | generic-object;

fragment = 'fragment', ' ', free-text;

generic-object = 'object', ' ', free-text;

surface = 'obverse' | 'reverse' | 'left' | 'right' | 'top' | 'bottom'
        | face | generic-surface | edge;

face = 'face', ' ', lower-case-letter;

edge = 'edge', ' ', lower-case-letter;

generic-surface = 'surface', ' ', free-text;

number = { decimal-digit }-;

loose = '(', free-text, ')';

ruling = ('single' | 'double' | 'triple'), ' ', 'ruling';

image = '(image ' number, [ lower-case-letter ], ' = ', free-text, ')';
```

See: [ATF Structure Tutorial](http://oracc.museum.upenn.edu/doc/help/editinginatf/primer/structuretutorial/index.html)

## Text

Text is a series of tokens separated by a word separator (space). The separator
can sometimes be omitted.

| Token Type   | Definition | Lemmatizable | Alignable | Notes |
| -------------|------------|--------------|-----------|-------|
| Tabulation   | `($___$)` | No | No | |
| Column       | `&` or `&` followed by numbers | No | No | |
| Divider      | `\|`, `:'`, `:"`, `:.`, `::`, `:?`, `:`, `;`, or `/` | No | No | Must be followed by the separator or end of the line. Can be followed by flags and modifiers and surrounded with broken away. |
| Commentary Protocol | `!qt`, `!bs`, `!cm`, or `!zz` | No | No | See  Commentary Protocols below. |
| Shift | `%` followed by one or more word characters | No | No | See Shifts below for a list of supported codes. |
| Erasure | `°` + erased words + `\` +  words written over erasure+ `°` | Special | Special | Must be followed by a separator or end of line. Erasure markers and erased words are not lemmatizable or alignable, but words written over erasure can be. |
| Word | Readings or graphemes separated by a joiner. | Maybe | Maybe | See Word below for full definition. |
| Lone Determinative | A word consisting only a determinative part. | No | No | See Word and Glosses below. |
| Unknown Number of Signs | `...` | No | No | |
| Document Oriented Gloss | `{(` or `)}` | No | No | See Glosses below. |
| Removal | `<<`, `>>` | No | No | See Presence below. |
| Omission| `<(`, `<`, `)>`, or `>` | No | No | See Presence below. |
| Broken Away | `[` or `]`| No | No | See Presence below. |
| Perhaps Broken Away | `(` or `)` | No | No | See Presence below. |
| ~~Line Continuation~~ | `→` | No | No | Must be at the end of the line. Will be replaced by a $-line in the future.

```ebnf
text = token, { [ word-separator ], token },
       [ word-separator, line-continuation ];
       (* Word seprator can be ommitted after an opening bracket or before 
          a closing bracket. Commentary protocols and dividers must be
          surrounded by word separators. *)

line-continuation = '→';

token = commentary-protocol
      | divider
      | divider-variant
      | tabulation
      | column
      | shift
      | erasure
      | word
      | determinative
      | unknown-number-of-signs
      | close-broken-away
      | close-perhaps-broken-away
      | close-intentional-omission
      | close-accidental-omission
      | close-removal
      | close-document-orionted-gloss
      | open-broken-away
      | open-perhaps-broken-away
      | open-intentional-omission
      | open-accidental-omission
      | open-removal
      | open-document-oriented-gloss;
           
tabulation = '($___$)';

column = '&', { decimal-digit };

divider-variant = ( variant-part | divider ), variant-separator,
                  ( variant-part | divider );
divider = divider-symbol, modifier, flag;
divider-symbol = '|' | ":'" | ':"' | ':.' | '::' | ':?' | ':' | ';' | '/';

commentary-protocol = '!qt' | '!bs' | '!cm' | '!zz';

document-oriented-gloss = '{(', token, { [word-separator], token } ,')}';

shift = '%', { word-character }-;

erasure = '°', [ erasure-part ] '\', [ erasure-part ], '°';
erasure-part = ( divider | word | lone-determinative ),
               { word-separator, ( divider | word | lone-determinative ) };

open-intentional-omission = '<(';
close-intentional-omission = ')>';
open-accidental-omission = '<';
close-accidental-omission = '>';
open-removal = '<<';
close-removal = '>>';

broken-away = open-broken-away-open | close-broken-away;
open-broken-away = '[';
close-broken-away = ']';

perhaps-broken-away = open-perhaps-broken-away | close-perhaps-broken-away;
open-perhaps-broken-away = '(';
close-perhaps-broken-away = ')';

word-separator = ' ';
```

See: [ATF Inline Tutorial](http://oracc.museum.upenn.edu/doc/help/editinginatf/primer/inlinetutorial/index.html)
and [ATF Quick Reference](http://oracc.museum.upenn.edu/doc/help/editinginatf/quickreference/index.html)

### Presence

A presence cannot be nested within itself.

| Presence Type | Open | Close | Scope | Constraint | Semantics |
| --------------|------|-------|-------|------------|-----------|
| Intentional Omission | `<(` | `)>` | Top-level, Word | Cannot be inside *Accidental Omission*. | |
| Accidental Omission | `<` | `>` | Top-level, Word| Cannot be inside *Intentional Omission*. | |
| Removal | `<<` | `>>` | Top-level, Word | | |
| Broken Away | `[` | `]`| Top-level, Word, Grapheme | Cannot be inside *Perhaps Broken Away* (E.g. `(x) [(x)] (x)` not `(x [x] x)`). | |
| Perhaps Broken Away | `(` | `)` | Top-level, Word | Can be inside of *Broken Away*, and must be fully in or out (E.g. `[(x)] (x)` not `[(x] x)`). Cannot be inside *Accidental Omission* or *Intentional Omission*. | |

See: [ATF Inline Tutorial](http://oracc.museum.upenn.edu/doc/help/editinginatf/primer/inlinetutorial/index.html)

### Glosses

Glosses cannot be nested within other glosses in the same scope.

| Gloss Type | Open | Close | Scope | Constraints | Semantics | Examples |
|------------|------|-------|-------|-------------|-----------|----------|
| Document Oriented Gloss | `{(` | `)}` | Top-level | | | `{(1(u))}` `{(%a he-pi₂ eš-šu₂)}` |
| Linguistic Gloss | `{{` | `}}` | Word | | | `du₃-am₃{{mu-un-<(du₃)>}}` |
| Determinative | `{` | `}` | Word | | | `{d}utu` `larsa{ki}` |
| Phonetic Gloss | `{+` | `}` | Word | Cannot appear alone. | | `{+u₃-mu₂}u₂-mu₁₁` `AN{+e}` |

See: [ATF Inline Tutorial](http://oracc.museum.upenn.edu/doc/help/editinginatf/primer/inlinetutorial/index.html)

### Commentary protocols

The Commentary protocol is used to change the display color of the text that
follows it. It has to be declared at the beginning of every line. Once declared,
it is valid until another protocol replaces it.

| Protocol | Description |
|----------|-----------|
| `!qt` | `Quotation` |
| `!bs` | `Base Text` |
| `!cm` | `Commentary` |
| `!zz` | `Uncertain` |

See: [Base Text and Commentary](http://oracc.museum.upenn.edu/doc/help/editinginatf/commentary/index.html)

### Shifts

Shifts change the language and normalization of the subsequent words until
another shift or the end of the line. If no shifts are present *Akkadian* is
used as the default language.

| Shift | Language | Dialect | Normalized |
| ------|----------|---------|------------|
| `%n` | Akkadian | | Yes |
| `%ma` | Akkadian | Middle Assyrian | No |
| `%mb` | Akkadian | Middle Babylonian | No |
| `%na` | Akkadian | Neo-Assyrian | No |
| `%nb` | Akkadian | Neo-Babylonian | No |
| `%lb` | Akkadian | Late Babylonian | No |
| `%sb` | Akkadian | Standard Babylonian | No |
| `%a` | Akkadian | | No |
| `%akk` | Akkadian | | No |
| `%eakk` | Akkadian | Early Akkadian | No |
| `%oakk` | Akkadian | Old Akkadian | No |
| `%ur3akk` | Akkadian | Ur III Akkadian | No |
| `%oa` | Akkadian | Old Assyrian | No |
| `%ob` | Akkadian | Old Babylonian | No |
| `%sux` | Sumerian | | No |
| `%es` | Sumerian | Emesal | No |
| `%e` | Sumerian | Emesal | No |

Any other shifts are considered valid and have language *Unknown*. *Akkadian*
and *Unknown* are lemmatizable.

### Word

A word is considered partial if starts or end ends with `-`, `.`, or `+`. 
A *lone determinative* is a special case of a word consisting only a single
determinative. A word is lemmatizable and alignable if:

- It is not erased.
- It is not partial.
- It is not lone determinative.
- It does not contain variants.
- It does not contain unclear signs.
- It does not contain unidentified signs.
- The language is lemmatizable.
- The language is not normalized.

```ebnf
word = [ joiner ], [ open-any ],
       ( inline-erasure | parts ), { part-joiner, ( inline-erasure | parts ) },
       [ close-any ], [ joiner ];
 
inline-erasure = '°', [ parts ], '\', [ parts ], '°';

parts = ( variant | determinative | linguistic-gloss | phonetic-gloss | 
          unknown-number-of-signs ),
        { [ part-joiner ], ( variant | determinative | linguistic-gloss | 
                             phonetic-gloss | unknown-number-of-signs ) };
        (* Word cannot consist of only unknown-number-of-signs. *)

linguistic-gloss = '{{', gloss-body, '}}';
phonetic-gloss = '{+', gloss-body, '}';
determinative = '{', gloss-body, '}';
gloss-body = [ open_any ] variant,  { part-joiner, variant }, [ close_any ]

part-joiner = [ inword-newline ], [ close_any ], [ joiner ], [ open_any ];
 
open_any = { open-broken-away
             | open-perhaps-away     
             | open-intentional-omission
             | open-accidental-omission
             | open-removal }+; 
close_any = { close-broken-away
             | close-perhaps-away     
             | close-intentional-omission
             | close-accidental-omission
             | close-removal }+;         
joiner = '-' | '+' | '.' | ':';
inword-newline = ';';

variant = variant-part, { variant-separator , variant-part };
variant-part = unknown 
             | value-with-sign
             | value
             | compound-grapheme
             | logogram
             | surrogate
             | number;

number = decimal-digit, { [ invalue-broken-away ], decimal-digit },
         modifier, flag;

surrogate = logogram, ['<(', value, { '-', value } ,')>'];
logogram = logogram-character, { [ invalue-broken-away ], logogram-character },
           [ sub-index ], modifier, flag;
logogram-character = 'A' | 'Ā' | 'Â' | 'B' | 'D' | 'E' | 'Ē' | 'Ê' | 'G' | 'H'
                   | 'I' | 'Ī' | 'Î' | 'Y' | 'K' | 'L' | 'M' | 'N' | 'P' | 'Q'
                   | 'R' | 'S' | 'Ṣ' | 'Š' | 'T' | 'Ṭ' | 'U' | 'Ū' | 'Û' | 'W'
                   | 'Z' | 'Ḫ' | 'ʾ';

value-with-sign = ( value | logogram ), '(', ( compound-grapheme | grapheme ),
                  ')';
value = value-character, { [ invalue-broken-away ], value-character }, 
        [ sub-index ], modifier, flag;
value-character = 'a' | 'ā' | 'â' | 'b' | 'd' | 'e' | 'ē' | 'ê' | 'g' | 'h'
                | 'i' | 'ī' | 'î' | 'y' | 'k' | 'l' | 'm' | 'n' | 'p' | 'q'
                | 'r' | 's' | 'ṣ' | 'š' | 't' | 'ṭ' | 'u' | 'ū' | 'û' | 'w'
                | 'z' | 'ḫ' | 'ʾ' | decimal-digit;
sub-index = { sub-index-character }-;

compound-grapheme = '|', compound-part, { compound-operator, compound-part },
                    '|';
compound-part = '(' grapheme-variant { compound-operator, grapheme-variant } ')'
              | grapheme-variant
grapheme-variant = grapheme, { variant-separator, grapheme };
compound-operator = '.' | '×' | '%' | '&' | '+';

grapheme = grapheme-character, 
           { [ invalue-broken-away ], grapheme-character },
           modifier,
           flag;
grapheme-character = word-character
                   | 'Ṣ' | 'Š' | 'Ṭ' 
                   | 'ṣ' | 'š' | 'ṭ'
                   | decimal-digit
                   | sub-index-character - 'ₓ';

unknown-number-of-signs = '...';
unknown = ('X' | 'x'), flag;

invalue-broken-away: open-broken-away | close-broken-away;

variant-separator = '/';

flag = { '!' | '?' | '*' | '#' };
modifier = { '@', ( 'c' | 'f' | 'g' | 's' | 't' | 'n' 
                  | 'z' | 'k' | 'r' | 'h' | 'v' | { decimal-digit }- ) };

sub-index-character = '₀' | '₁' | '₂' | '₃' | '₄' | '₅' 
                    | '₆' | '₇' | '₈' | '₉' | 'ₓ';
```

## Validation

The ATF should be parseable using the specification above. In addition,
all readings and signs must be correct according to our sign list. Sometimes
when the validation or parsing logic is updated existing transliterations can
become invalid. It should still be possible to load these transliterations, but
saving them results in an error until the syntax is corrected.

## Labels

```ebnf

line-number-label = { not-space }-;

column-label = roman-numeral, { status };
roman-numeral = { 'i' | 'v' | 'x' | 'l' | 'c' | 'd' | 'm' }-;
                (* Must be a valid numeral. *)

surface-label = ( 'o' | 'r' | 'b.e.' | 'e.' | 'l.e.' | 'r.e.' | 't.e.' ),
                { status };

status = "'" | '?' | '!' | '*';
```

See: [Labels](http://oracc.museum.upenn.edu/doc/help/editinginatf/labels/index.html)
and [ATF Structure Tutorial](http://oracc.museum.upenn.edu/doc/help/editinginatf/primer/structuretutorial/index.html)
