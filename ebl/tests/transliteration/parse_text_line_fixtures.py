from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.sign_tokens import (
    Number,
)
from ebl.transliteration.domain.tokens import (
    ValueToken,
)


DEFAULT_LANGUAGE = Language.AKKADIAN


def create_number_part(number: str) -> Number:
    return Number.of((ValueToken.of(number),))
