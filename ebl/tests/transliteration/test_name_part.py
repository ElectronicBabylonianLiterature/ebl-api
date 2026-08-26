from typing import Any, Dict, List, cast

import pytest

from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.application.token_schemas_signs import NamedSignSchema
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.sign_token_base import (
    NamePart,
    convert_name_parts,
)
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.tokens import Token, ValueToken


def test_a_value_token_contributes_its_text_to_the_name() -> None:
    part = NamePart.of(ValueToken.of("ku"))

    assert part.name_contribution == "ku"
    assert part.value == "ku"


def test_a_bracket_contributes_nothing_to_the_name() -> None:
    bracket = BrokenAway.open()
    part = NamePart.of(bracket)

    assert part.name_contribution == ""
    assert part.value == bracket.value


def test_a_name_contribution_that_disagrees_with_its_token_is_rejected() -> None:
    with pytest.raises(ValueError, match="does not match"):
        NamePart(ValueToken.of("kur"), "totally wrong")


def test_a_bracket_may_not_claim_a_name_contribution() -> None:
    with pytest.raises(ValueError, match="does not match"):
        NamePart(BrokenAway.open(), "[")


def test_converting_name_parts_is_idempotent() -> None:
    tokens = (ValueToken.of("ku"), BrokenAway.open(), ValueToken.of("r"))
    converted = convert_name_parts(tokens)

    assert convert_name_parts(converted) == converted
    assert tuple(part.token for part in converted) == tokens


def test_a_name_part_is_not_a_token() -> None:
    part = NamePart.of(ValueToken.of("ku"))

    assert not isinstance(part, Token)


def test_a_named_sign_serializes_its_name_tokens_not_its_name_parts() -> None:
    reading = Reading.of((ValueToken.of("ku"), BrokenAway.open(), ValueToken.of("r")))
    dumped = cast(Dict[str, Any], NamedSignSchema().dump(reading))

    assert dumped["nameParts"] == OneOfTokenSchema().dump(
        list(reading.name_tokens), many=True
    )


def test_a_name_part_is_not_serializable_as_a_token() -> None:
    part = NamePart.of(ValueToken.of("ku"))

    dumped = cast(List[Any], OneOfTokenSchema().dump([part], many=True))

    assert dumped != OneOfTokenSchema().dump([part.token], many=True)
    assert dumped[0][1] == {"_schema": "Unsupported object type: NamePart"}
