from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain.tokens import ErasureState, Token


def assert_token_serialization(token: Token, serialized: dict) -> None:
    with_clean_value = {
        "erasure": ErasureState.NONE.name,
        "cleanValue": token.clean_value,
        **serialized,
    }
    assert OneOfTokenSchema().dump(token) == with_clean_value  # pyre-ignore[16]
    assert OneOfTokenSchema().load(with_clean_value) == token  # pyre-ignore[16]
