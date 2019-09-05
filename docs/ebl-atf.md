eBL-ATF is based on [Oracc-ATF](http://oracc.museum.upenn.edu/doc/help/editinginatf/index.html) but is not fully compatible with other ATF flavours. eBL-ATF uses UTF-8 encoding. The grammar definitions below use [EBNF](https://en.wikipedia.org/wiki/Extended_Backus–Naur_form) ([ISO/IEC 14977 : 1996(E)](https://standards.iso.org/ittf/PubliclyAvailableStandards/s026153_ISO_IEC_14977_1996(E).zip)). eBL-ATF can be empty or consist of lines separated by a newline character.

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
| Document Oriented Gloss | `{(` or `)}` | No | No | See Glosses below. |
| Shift | `%` followed by one or more word characters | No | No | See Shifts below for a list of supported codes. |
| Erasure | `°` + erased words + `\` +  words written over erasure+ `°` | Special | Special | Must be followed by a separator or end of line. Erasure markers and erased words are not lemmatizable or alignable, but words written over erasure can be. |
| Word | Readings or graphemes separated by a joiner. | Maybe | Maybe | See Word below for full definition. |
| Lone Determinative | A word consisting only a determinative part. | No | No | See Glosses below. |
| Omission or Removal | `<<`, `<(`, `<`, `>>`, `)>`, or `>` | No | No | See Presence below. |
| Broken Away | `[` or `]`| No | No | See Presence below. |
| Perhaps Broken Away | `(` or `)` | No | No | See Presence below. |
| Unknown Number of Signs | `...` | No | No | |
| Line Continuation | `→` | No | No | Must be at the end of the line. Will be replaced by a $-line in the future.

```ebnf
text = [ token, { [word-separator], token } ], [ line-continuation ];

line-continuation = '→';

token = tabulation
      | column
      | divider, ( word-separator | eol ) 
      | commentary-protocol
      | document-oriented-gloss
      | shift
      | erasure, ( word-separator | eol ) 
      | word
      | lone-determinative
      | omission
      | broken-away
      | perhaps-broken-away
      | unknown-number-of-signs;

tabulation = '($___$)';

column = '&', { decimal-digit };

divider = [ iniline-broken-away ], divider-symbol, modifier, flag, [ iniline-broken-away ];
divider-symbol = '|' | ":'" | ':"' | ':.' | '::' | ':?' | ':' | ';' | '/';

commentary-protocol = '!qt' | '!bs' | '!cm' | '!zz';

document-oriented-gloss = '{(' | ')}';

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

| Presence Type | Open | Close | Scope | Constraint |
| --------------|------|-------|-------|------------|
| Intentional Omission | `<(` | `)>` | Top-level, Word | Cannot be inside *Accidental Omission*. |
| Accidental Omission | `<` | `>` | Top-level, Word| Cannot be inside *Intentional Omission*. |
| Perhaps Broken Away | `(` | `)` | Top-level, Word, Grapheme | Should be inside *Accidental Omission*. |
| Removal | `<<` | `>>` | Top-level, Word | |
| Broken Away | `[` | `]`| Top-level, Word, Grapheme |
| Perhaps Broken Away | `(` | `)` | Top-level, Word, Grapheme | Should be inside *Broken Away*. |

See: [ATF Inline Tutorial](http://oracc.museum.upenn.edu/doc/help/editinginatf/primer/inlinetutorial/index.html)

### Glosses

Glosses cannot be nested within other glosses in the same scope.

| Gloss Type | Open | Close | Scope |
|------------|------|-------|-------|
| Document Oriented Gloss | `{(` | `)}` | Top-level |
| Linguistic Gloss | `{{` | `}}` | Word |
| Determinative | `{+` | `}` | Word |
| Phonetic Gloss | `{+` | `}` | Word |

See: [ATF Inline Tutorial](http://oracc.museum.upenn.edu/doc/help/editinginatf/primer/inlinetutorial/index.html)

### Commentary protocols

| Protocol |
|----------|
| `!qt` |
| `!bs` |
| `!cm` |
| `!zz` |

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
lone-determinative = [ omission ],
                     open-determinative,
                     [ broken-away-open ],
                     variant, { { joiner }, variant }
                     [ broken-away-close ],
                     close-determinative,
                     [ omission ];

word = [ { joiner }-, open-iniline-broken-away ],
       [ open-omission ],
       ( inline-erasure, { part-joiner, inline-erasure | parts } | parts )
       [ close-omission ],
       [ close-inline-broken-away, { joiner }- ];
 
inline-erasure = '°', [ parts ], '\', [ parts ], '°';

parts = variant,  { part-joiner, ( determinative | variant ) }
      | determinative, { part-joiner,  ( determinative | variant )}-;

determinative = [ omission ],
                open-determinative,
                [ open-broken-away ],
                variant,  { part-joiner, variant },
                [ close-broken-away ],
                close-determinative
                [ omission ];
open-determinative = '{+' | '{';
close-determinative = '}';

part-joiner = [ close-iniline-broken-away ],
              [ close-omission ],
              { joiner },
              [ open-omission ],
              [ open-iniline-broken-away ];

joiner = linguistic-gloss | '-' | '+' | '.';
linguistic-gloss = '{{' | '}}';

variant = variant-part, { variant-separator , variant-part };
variant-part = unknown | value-with-sign | value | compound-grapheme | grapheme | divider;

value-with-sign = value, [ '!' ], '(', compound-grapheme, ')';

value = value-character, { [ iniline-broken-away ], value-character }, [ sub-index ], modifier, flag;
value-character = 'a' | 'ā' | 'â' | 'b' | 'd' | 'e' | 'ē' | 'ê' | 'g' | 'h' | 'i'
                | 'ī' | 'î' | 'y' | 'k' | 'l' | 'm' | 'n' | 'p' | 'q' | 'r' | 's'
                | 'ṣ' | 'š' | 't' | 'ṭ' | 'u' | 'ū' | 'û' | 'w' | 'z' | 'ḫ' | 'ʾ'
                | decimal-digit;
sub-index = { sub-index-character }-;

compound-grapheme = [ '|' ],
                    compound-part, { { compound-operator }, compound-part },
                    [ '|' ];
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
