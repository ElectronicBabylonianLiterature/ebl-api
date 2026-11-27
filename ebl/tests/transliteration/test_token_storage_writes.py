from typing import Any, List

import pytest

from ebl.tests.fragmentarium.stored_line_shapes import (
    DERIVED_TOKEN_FIELDS,
    TOKEN_LOAD_DEFAULTS,
    is_token,
    sparse_tokens,
)
from ebl.tests.transliteration.storage_test_helpers import has_key, stored_dump
from ebl.tests.transliteration.test_token_load_defaults import (
    ALIGNED_WORD,
    TOKENS,
    api_dump,
)
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain.tokens import Token

NON_DEFAULT_WORD_FIELDS = {
    "alignment",
    "variant",
    "hasVariantAlignment",
    "hasOmittedAlignment",
    "namedEntities",
    "realia",
}


def stored_token(token: Token) -> dict:
    return stored_dump(OneOfTokenSchema(), token)


def token_values(document: Any, key: str) -> List[Any]:
    if isinstance(document, list):
        return [value for item in document for value in token_values(item, key)]
    if not isinstance(document, dict):
        return []
    own = [document[key]] if is_token(document) and key in document else []
    return own + token_values(list(document.values()), key)


STORED_TOKENS = [stored_token(token) for token in TOKENS]


@pytest.mark.parametrize("token", TOKENS, ids=lambda token: type(token).__name__)
def test_a_stored_token_has_the_sparse_shape(token: Token) -> None:
    assert stored_token(token) == sparse_tokens(api_dump(token))


@pytest.mark.parametrize("token", TOKENS, ids=lambda token: type(token).__name__)
def test_a_stored_token_loads_equal_to_the_token(token: Token) -> None:
    assert OneOfTokenSchema().load(stored_token(token)) == token


@pytest.mark.parametrize("key", sorted(DERIVED_TOKEN_FIELDS))
def test_derived_fields_are_never_stored(key: str) -> None:
    assert has_key([api_dump(token) for token in TOKENS], key)
    assert not has_key(STORED_TOKENS, key)


@pytest.mark.parametrize("key", sorted(TOKEN_LOAD_DEFAULTS))
def test_no_stored_token_holds_a_default_value(key: str) -> None:
    assert TOKEN_LOAD_DEFAULTS[key] not in token_values(STORED_TOKENS, key)


def test_non_default_word_fields_are_stored() -> None:
    assert NON_DEFAULT_WORD_FIELDS <= set(stored_token(ALIGNED_WORD))


@pytest.mark.parametrize("key", sorted(TOKEN_LOAD_DEFAULTS))
def test_api_dumps_keep_every_default_field(key: str) -> None:
    assert has_key([api_dump(token) for token in TOKENS], key)
