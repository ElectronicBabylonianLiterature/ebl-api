from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain.tokens import ErasureState, Token


def assert_token_serialization(token: Token, serialized: dict) -> None:
    with_common_properties = {
        "erasure": ErasureState.NONE.name,
        "value": token.value,
        "cleanValue": token.clean_value,
        "enclosureType": [type_.name for type_ in token.enclosure_type],
        **serialized,
    }
    assert OneOfTokenSchema().dump(token) == with_common_properties
    assert OneOfTokenSchema().load(with_common_properties) == token
