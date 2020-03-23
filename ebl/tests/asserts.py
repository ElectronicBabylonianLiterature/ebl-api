from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain.tokens import Token


def assert_token_serialization(token: Token, serialized: dict) -> None:
    assert OneOfTokenSchema().dump(token) == serialized
    assert OneOfTokenSchema().load(serialized) == token
