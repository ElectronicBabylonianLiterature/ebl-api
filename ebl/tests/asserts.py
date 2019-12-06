from ebl.transliteration.application.token_schemas import dump_token, load_token
from ebl.transliteration.domain.tokens import Token


def assert_token_serialization(token: Token, serialized: dict) -> None:
    assert dump_token(token) == serialized
    assert load_token(serialized) == token
