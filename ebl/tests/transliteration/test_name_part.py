from typing import Any, Dict, List, cast

from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.application.token_schemas_signs import NamedSignSchema
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.sign_token_base import (
    NamePart,
    convert_name_parts,
    name_parts_of,
)
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.tokens import Token, ValueToken


def test_a_value_token_contributes_its_text_to_the_name() -> None:
    part = NamePart(ValueToken.of("ku"))

    assert part.name_contribution == "ku"
    assert part.value == "ku"


def test_a_bracket_contributes_nothing_to_the_name() -> None:
    bracket = BrokenAway.open()
    part = NamePart(bracket)

    assert part.name_contribution == ""
    assert part.value == bracket.value


def test_a_name_contribution_always_agrees_with_its_token() -> None:
    for token in (ValueToken.of("kur"), BrokenAway.open(), BrokenAway.close()):
        part = NamePart(token)

        assert part.name_contribution == (
            token.value if isinstance(token, ValueToken) else ""
        )


def test_wrapping_tokens_keeps_them_in_order() -> None:
    tokens = (ValueToken.of("ku"), BrokenAway.open(), ValueToken.of("r"))
    parts = name_parts_of(tokens)

    assert tuple(part.token for part in parts) == tokens


def test_converting_name_parts_only_materializes_them() -> None:
    parts = name_parts_of((ValueToken.of("ku"), BrokenAway.open()))

    assert convert_name_parts(iter(parts)) == parts
    assert convert_name_parts(parts) == parts


def test_a_name_part_is_not_a_token() -> None:
    part = NamePart(ValueToken.of("ku"))

    assert not isinstance(part, Token)


def test_a_named_sign_serializes_its_name_tokens_not_its_name_parts() -> None:
    reading = Reading.of((ValueToken.of("ku"), BrokenAway.open(), ValueToken.of("r")))
    dumped = cast(Dict[str, Any], NamedSignSchema().dump(reading))

    assert dumped["nameParts"] == OneOfTokenSchema().dump(
        list(reading.name_tokens), many=True
    )


def test_a_name_part_is_not_serializable_as_a_token() -> None:
    part = NamePart(ValueToken.of("ku"))

    dumped = cast(List[Any], OneOfTokenSchema().dump([part], many=True))

    assert dumped != OneOfTokenSchema().dump([part.token], many=True)
    assert dumped[0][1] == {"_schema": "Unsupported object type: NamePart"}


def test_with_name_tokens_rewraps_the_name() -> None:
    reading = Reading.of_name("ku")
    replacement = (ValueToken.of("n"), BrokenAway.open(), ValueToken.of("u"))

    updated = reading.with_name_tokens(replacement)

    assert updated.name_tokens == replacement
    assert updated.name_parts == name_parts_of(replacement)
    assert updated.name == "nu"


def test_with_sign_replaces_only_the_sign() -> None:
    reading = Reading.of_name("ku")
    sign = ValueToken.of("KU")

    updated = reading.with_sign(sign)

    assert updated.sign == sign
    assert updated.name_parts == reading.name_parts
    assert reading.sign is None
