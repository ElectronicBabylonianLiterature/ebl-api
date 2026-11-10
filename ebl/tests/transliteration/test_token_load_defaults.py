import json
from typing import Any, Iterable, List, Set, cast

import pytest

from ebl.dictionary.domain.word import WordId
from ebl.tests.fragmentarium.stored_line_shapes import (
    DERIVED_TOKEN_FIELDS,
    TOKEN_LOAD_DEFAULTS,
    TOKEN_TYPES,
    sparse_tokens,
)
from ebl.tests.transliteration.storage_test_helpers import stored_dump
from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain.atf import Flag
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
from ebl.transliteration.domain.enclosure_tokens import Emendation
from ebl.transliteration.domain.normalized_akkadian import Caesura
from ebl.transliteration.domain.sign import SignName
from ebl.transliteration.domain.sign_tokens import Grapheme, Logogram, Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import (
    CommentaryProtocol,
    Token,
    Tabulation,
    ValueToken,
    WordOmitted,
)
from ebl.transliteration.domain.word_tokens import InWordNewline, Word

ATF_LINES = [
    "1. ku-[nu]-uš KUR#! ⸢ki⸣ {d}INANA {+mu}AN.KU₃",
    "1. ku-x-X ... (ku) <<ku>> <(ku)> <ku> {(ku)}",
    "1. °ku\\ra° ku/ra 30 MUŠ₂(|U.U|) |KUR×KUR|",
    "1. :.@v ku",
    "1. | ku ; ku",
    "1. ku-{{ku}}-ra",
    "1. %n ibnû | ibnû (|) ibnû ...",
    "1. %grc ΑΒ",
    "1. {d}",
    "1. ku • ku",
    "1. ku :? ku",
    "1. ku &1 ku",
    "1. ku-ra₂{+ku}",
    "1. ku // ra",
    "1. %es ku",
]
ALIGNED_WORD = Word.of(
    [Reading.of_name("ku")],
    unique_lemma=(WordId("ku I"),),
    alignment=1,
    variant=Word.of([Reading.of_name("ra")]),
    has_variant_alignment=True,
    has_omitted_alignment=True,
    named_entities=("Entity-1",),
    realia=("Realia-1",),
)
UNPARSED_TOKENS = [
    ALIGNED_WORD,
    Logogram.of_name("KUR").with_surrogate([Reading.of_name("kur")]),
    Reading.of_name("ku").with_sign(Grapheme.of(SignName("KU"))),
    Grapheme.of(SignName("KUR"), ("v",), (Flag.DAMAGE,)),
    Tabulation.of(),
    CommentaryProtocol.of("!qt"),
    WordOmitted.of(),
    InWordNewline.of(),
    Emendation.open(),
    Caesura.certain(),
]
LINES = [cast(TextLine, parse_atf_lark(atf).lines[0]) for atf in ATF_LINES]
TOKENS = [*UNPARSED_TOKENS, *(token for line in LINES for token in line.content)]


def api_dump(token: Token) -> dict:
    return cast(dict, OneOfTokenSchema().dump(token))


def dumped_types(value: Any) -> Set[str]:
    if isinstance(value, list):
        return set().union(*(dumped_types(item) for item in value))
    if not isinstance(value, dict):
        return set()
    own = {value["type"]} if isinstance(value.get("type"), str) else set()
    return own.union(*(dumped_types(item) for item in value.values()))


def key_count(document: Any, key: str) -> int:
    return json.dumps(document).count(f'"{key}"')


def full_dumps(tokens: Iterable[Token]) -> List[dict]:
    return [api_dump(token) for token in tokens]


def test_the_samples_cover_every_token_type():
    assert TOKEN_TYPES - {"Token"} <= dumped_types(full_dumps(TOKENS))


@pytest.mark.parametrize("key", [*TOKEN_LOAD_DEFAULTS, *sorted(DERIVED_TOKEN_FIELDS)])
def test_the_samples_omit_every_omittable_field(key):
    full = full_dumps(TOKENS)

    assert key_count(sparse_tokens(full), key) < key_count(full, key)


@pytest.mark.parametrize("token", TOKENS, ids=lambda token: type(token).__name__)
def test_a_sparse_token_loads_equal_to_the_full_token(token):
    assert OneOfTokenSchema().load(sparse_tokens(api_dump(token))) == token


def test_a_sparse_legacy_token_loads_as_a_value_token():
    assert OneOfTokenSchema().load({"type": "Token", "value": "ku"}) == ValueToken.of(
        "ku"
    )


def test_non_default_values_are_not_omitted():
    sparse = sparse_tokens(api_dump(ALIGNED_WORD))

    assert {
        "alignment",
        "variant",
        "hasVariantAlignment",
        "hasOmittedAlignment",
        "namedEntities",
        "realia",
    } <= set(sparse)


@pytest.mark.parametrize("line", LINES, ids=ATF_LINES)
@pytest.mark.parametrize(
    "dump",
    [OneOfLineSchema().dump, lambda line: stored_dump(OneOfLineSchema(), line)],
    ids=["api", "storage"],
)
def test_a_sparse_line_loads_equal_to_the_full_line(line, dump):
    assert OneOfLineSchema().load(sparse_tokens(dump(line))) == line
