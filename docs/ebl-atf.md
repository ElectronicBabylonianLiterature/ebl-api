eBL-ATF is based on [Oracc-ATF](http://oracc.museum.upenn.edu/doc/help/editinginatf/index.html) but is not fully compatible with other ATF flavours. eBL-ATF uses UTF-8 encoding. The grammar definitions below use [EBNF](https://en.wikipedia.org/wiki/Extended_Backus–Naur_form) ([ISO/IEC 14977 : 1996(E)](https://standards.iso.org/ittf/PubliclyAvailableStandards/s026153_ISO_IEC_14977_1996(E).zip)). 

The EBNF grammar below is an idealized representation of the eBL-ATF as it does not deal with ambiguities and implentattional details necessary to create the domain model in practice. A fully functional grammar is defined in [ebl-atf.lark](https://github.com/ElectronicBabylonianLiterature/ebl-api/blob/master/ebl/text/ebl-atf.lark). The file uses the EBNF variant of the [Lark parsing library](https://github.com/lark-parser/lark). See [Grammar Reference](https://lark-parser.readthedocs.io/en/latest/grammar/) and [Lark Cheat Sheet](https://lark-parser.readthedocs.io/en/latest/lark_cheatsheet.pdf).


eBL-ATF can be empty or consist of lines separated by a newline character.

```ebnf
ebl-atf = [ line, { '\n', line } ];

word-character = ? A-Za-z ?;
decimal-digit = '0' | '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9';
eol = ? end of line ?;
```

## Lines

A line can be either *empty*, *control* or *text line*. Text lines contain transliterated text. Other lines do not currently have special semantics.  Continuation lines (starting with space) are not supported. 

```ebnf
line = empty-line
     | control-line
     | text-line;

empty-line = '';

control-line = '=:' | '$' | '@' | '&' | '#', { any-character };

text-line = line-number, ' ', text;
line-number = { not-space }-, '.';
not-space = any-character - ' ';

any-character = ? any UTF-8 character ?;
```

See: [ATF Structure Tutorial](http://oracc.museum.upenn.edu/doc/help/editinginatf/primer/structuretutorial/index.html)

## Text

Text is a series of tokens separated by a word separator (space). The separator can sometimes be omitted.

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
| Line Continuation | `→` | No | No | Must be at the end of the line. Will be replaced by a $-line in the future.

```ebnf
text = [ (token | document-oriented-gloss), { [word-separator], (token | document-oriented-gloss) } ], [ line-continuation ];

line-continuation = '→';

token = tabulation
      | column
      | divider, ( word-separator | eol ) 
      | commentary-protocol
      | shift
      | erasure, ( word-separator | eol ) 
      | word
      | determinative
      | omission
      | broken-away
      | perhaps-broken-away
      | unknown-number-of-signs;

tabulation = '($___$)';

column = '&', { decimal-digit };

divider = [ iniline-broken-away ], divider-symbol, modifier, flag, [ iniline-broken-away ];
divider-symbol = '|' | ":'" | ':"' | ':.' | '::' | ':?' | ':' | ';' | '/';

commentary-protocol = '!qt' | '!bs' | '!cm' | '!zz';

document-oriented-gloss = '{(', token, { [word-separator], token } ,')}';

shift = '%', { word-character }-;

erasure = '°', [ erasure-part ] '\', [ erasure-part ], '°';
erasure-part = ( divider | word | lone-determinative ), { word-separator, ( divider | word | lone-determinative ) };

omission = open-omission | close-omission;
open-omission = '<<' | '<(' | '<';
close-omission = '>>' | ')>' | '>';

broken-away = open-broken-away-open | close-broken-away;
open-broken-away = '[';
close-broken-away = ']';

perhaps-broken-away = open-perhaps-broken-away | close-perhaps-broken-away;
open-perhaps-broken-away = '(';
open-perhaps-broken-away = ')';

inline-broken-away = open-inline-broken-away | close-inline-broken-away;
open-inline-broken-away = '[('
                        | '['
                        | ? not { ?, '(', ? not . ?;
close-inline-broken-away = ? not . ?, ')]' 
                         | ')', ? not } ?
                         | ']';

unknown-number-of-signs = '...';

word-separator = ' ';
```

See: [ATF Inline Tutorial](http://oracc.museum.upenn.edu/doc/help/editinginatf/primer/inlinetutorial/index.html) and [ATF Quick Reference](http://oracc.museum.upenn.edu/doc/help/editinginatf/quickreference/index.html)

### Presence

A presence cannot be nested within itself.

| Presence Type | Open | Close | Scope | Constraint | Semantics |
| --------------|------|-------|-------|------------|-----------|
| Intentional Omission | `<(` | `)>` | Top-level, Word | Cannot be inside *Accidental Omission*. | |
| Accidental Omission | `<` | `>` | Top-level, Word| Cannot be inside *Intentional Omission*. | |
| Removal | `<<` | `>>` | Top-level, Word | | |
| Broken Away | `[` | `]`| Top-level, Word, Grapheme | |
| Perhaps Broken Away | `(` | `)` | Top-level, Word, Grapheme | Should be inside *Broken Away*. Cannot be inside *Accidental Omission* or *Intentional Omission*. | |

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

| Protocol | Semantics |
|----------|-----------|
| `!qt` | |
| `!bs` | |
| `!cm` | |
| `!zz` | |

### Shifts

Shifts change the language and normalization of the subsequent words until another shift or the end of the line. If no shifts are present *Akkadian* is used as the default language.

| Shift | Language | Normalized |
| ------|----------|------------|
| `%n` | Akkadian | Yes |
| `%ma` | Akkadian | No |
| `%mb` | Akkadian | No |
| `%na` | Akkadian | No |
| `%nb` | Akkadian | No |
| `%lb` | Akkadian | No |
| `%sb` | Akkadian | No |
| `%a` | Akkadian | No |
| `%akk` | Akkadian | No |
| `%eakk` | Akkadian | No |
| `%oakk` | Akkadian | No |
| `%ur3akk` | Akkadian | No |
| `%oa` | Akkadian | No |
| `%ob` | Akkadian | No |
| `%sux` | Sumerian | No |
| `%es` | Emesal | No |
| `%e` | Emesal | No |
| `%n` | Akkadian | No |

Any other shifts are considered valid and have language *Unknown*. *Akkadian* and *Unknown* are lemmatizable.

### Word

A word is considered partial if starts or end ends with `-`, `.`, or `+`. A *lone determinative* is a special case of a word consisting only a single determinative. A word is lemmatizable and alignable if:
- It is not erased.
- It is not partial.
- It is not lone determinative.
- It does not contain variants.
- It does not contain unclear signs.
- It does not contain unidentified signs.
- The language is lemmatizable.
- The language is not normalized.

```ebnf
word = [ joiner, open-iniline-broken-away | { determinative }- ],
       ( inline-erasure, { part-joiner, ( inline-erasure | parts ) } | parts )
       [ { determinative }- | close-inline-broken-away, joiner ];
 
inline-erasure = '°', [ parts ], '\', [ parts ], '°';

parts = ( variant | linguistic-gloss | phonetic-gloss ), { part-joiner, ( variant | linguistic-gloss | phonetic-gloss ) };

linguistic-gloss = '{{', word, { [ word-separator ], word }, '}}';
phonetic-gloss = '{+', variant,  { part-joiner, variant }, '}';

determinative = '{', variant,  { part-joiner, variant }, '}';

part-joiner = [ close-omission ],
              [ close-iniline-broken-away ],
              [ joiner ],
              [ open-iniline-broken-away ],
              [ open-omission ];
              
joiner = '-' | '+' | '.';


variant = variant-part, { variant-separator , variant-part };
variant-part = unknown | value-with-sign | value | compound-grapheme | logogram | divider;

logogram = logogram-character, { [ iniline-broken-away ], logogram-character }, [ sub-index ], modifier, flag;
logogram-character = 'A' | 'Ā' | 'Â' | 'B' | 'D' | 'E' | 'Ē' | 'Ê' | 'G' | 'H' | 'I'
                   | 'Ī' | 'Î' | 'Y' | 'K' | 'L' | 'M' | 'N' | 'P' | 'Q' | 'R' | 'S'
                   | 'Ṣ' | 'Š' | 'T' | 'Ṭ' | 'U' | 'Ū' | 'Û' | 'W' | 'Z' | 'Ḫ' | 'ʾ'
                   | decimal-digit;     

value-with-sign = value, '(', ( compound-grapheme | grapheme ), ')';
value = value-character, { [ iniline-broken-away ], value-character }, [ sub-index ], modifier, flag;
value-character = 'a' | 'ā' | 'â' | 'b' | 'd' | 'e' | 'ē' | 'ê' | 'g' | 'h' | 'i'
                | 'ī' | 'î' | 'y' | 'k' | 'l' | 'm' | 'n' | 'p' | 'q' | 'r' | 's'
                | 'ṣ' | 'š' | 't' | 'ṭ' | 'u' | 'ū' | 'û' | 'w' | 'z' | 'ḫ' | 'ʾ'
                | decimal-digit;
sub-index = { sub-index-character }-;

compound-grapheme = '|', compound-part, { { compound-operator }, compound-part }, '|';
compound-part = grapheme, { variant-separator, grapheme };
compound-operator = '.' | '×' | '%' | '&' | '+' | '(' | ')';

grapheme = [ '$' ], grapheme-character, 
           { [ iniline-broken-away ], grapheme-character },
           modifier,
           flag;
grapheme-character = word-character
                   | 'Ṣ' | 'Š' | 'Ṭ' 
                   | 'ṣ' | 'š' | 'ṭ'
                   | decimal-digit
                   | sub-index-character - 'ₓ';

unknown = ('X' | 'x'), flag;

variant-separator = '/';

flag = { '!' | '?' | '*' | '#' };
modifier = { '@', ( 'c' | 'f' | 'g' | 's' | 't' | 'n' | 'z'  | 'k' | 'r' | 'h' | 'v' | { decimal-digit }- ) };

sub-index-character = '₀' | '₁' | '₂' | '₃' | '₄' | '₅' | '₆' | '₇' | '₈' | '₉' | 'ₓ';
```

## Validation

The ATF should be parseable using the specification above. In addition, it must pass [pyoracc](https://github.com/oracc/pyoracc) validation and not contain unknown readings. To make the ATF valid according to pyoracc a fake header is added to the input:

```
&XXX = XXX
#project: eblo
#atf: lang akk-x-stdbab
#atf: use unicode
#atf: use math
#atf: use legacy
```

The only purpose of the header is to make the pyoracc accept the ATF and it is not saved to the database. To check the readings the ATF is stripped from all other characters except readings and graphemes. Each reading must match a value in the sign list.

Sometimes when the validation or parsing logic is updated existing transliterations can become invalid. It should still be possible to load these transliterations but saving them results in an error until the syntax has been corrected.

## Labels

```ebnf

line-number-label = { not-space }-;

column-label = roman-numeral, { status };
roman-numeral = { 'i' | 'v' | 'x' | 'l' | 'c' | 'd' | 'm' }-; (* Must be a valid numeral. *)

surface-label = ( 'o' | 'r' | 'b.e.' | 'e.' | 'l.e.' | 'r.e.' | 't.e.' ), { status };

status = "'" | '?' | '!' | '*';
```
See: [Labels](http://oracc.museum.upenn.edu/doc/help/editinginatf/labels/index.html) and [ATF Structure Tutorial](http://oracc.museum.upenn.edu/doc/help/editinginatf/primer/structuretutorial/index.html)
