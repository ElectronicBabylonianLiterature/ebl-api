from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.signs_transformer import name_arguments
from ebl.transliteration.domain.tokens import ValueToken, Variant


def broken_reading(head: str, tail: str) -> Reading:
    return Reading.of_arguments(
        name_arguments([ValueToken.of(head), BrokenAway.open(), ValueToken.of(tail)])
    )


VARIANT_WITH_UNPARSED_BREAK = Variant.of(
    Reading.of([ValueToken.of("k[ur")]),
    Reading.of([ValueToken.of("r[a")]),
)

VARIANT_WITH_PARSED_BREAK = Variant.of(
    broken_reading("k", "ur"),
    broken_reading("r", "a"),
)
