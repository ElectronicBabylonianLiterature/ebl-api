from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain.tokens import Token


def assert_token_serialization(token: Token, serialized: dict) -> None:
    with_clean_value = {
        "cleanValue": token.clean_value,
        **serialized
    }
    assert OneOfTokenSchema().dump(token) == with_clean_value  # pyre-ignore[16]
    assert OneOfTokenSchema().load(with_clean_value) == token  # pyre-ignore[16]
