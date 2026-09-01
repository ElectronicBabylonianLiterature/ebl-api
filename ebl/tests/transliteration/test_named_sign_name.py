from typing import Any, Dict, Sequence, cast

import pytest

import ebl.transliteration.application.token_schemas  # noqa: F401
from ebl.transliteration.application.token_schemas_signs import (
    NamedSignSchema,
    ReadingSchema,
)
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.sign_token_base import (
    NamedSignArguments,
    convert_name_breaks,
    convert_name_parts,
)
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.signs_transformer import name_arguments
from ebl.transliteration.domain.tokens import ValueToken

BROKEN_NAME = (ValueToken.of("k"), BrokenAway.close(), ValueToken.of("u"))


def _broken_reading() -> Reading:
    return Reading.of_arguments(name_arguments(BROKEN_NAME))


def test_the_name_is_the_value_tokens_only() -> None:
    reading = _broken_reading()

    assert reading.name_parts == (ValueToken.of("k"), ValueToken.of("u"))
    assert reading.name == "ku"


def test_a_break_is_held_in_its_own_array() -> None:
    reading = _broken_reading()

    assert reading.name_breaks == (BrokenAway.close(),)
    assert reading.name_breaks[0].value == "]"


def test_a_break_contributes_nothing_to_the_name() -> None:
    unbroken = Reading.of_name("ku")

    assert _broken_reading().name == unbroken.name
    assert _broken_reading().value != unbroken.value


def test_the_two_arrays_interleave_back_into_the_written_order() -> None:
    reading = _broken_reading()

    assert reading.name_tokens == BROKEN_NAME
    assert reading.value == "k]u"


def test_a_name_never_takes_more_breaks_than_parts() -> None:
    with pytest.raises(ValueError, match="at most 1 breaks, not 2"):
        Reading.of_arguments(
            NamedSignArguments(
                (ValueToken.of("ku"),),
                name_breaks=(BrokenAway.open(), BrokenAway.close()),
            )
        )


def test_a_trailing_break_is_kept_in_written_order() -> None:
    reading = Reading.of_arguments(
        name_arguments((ValueToken.of("ku"), BrokenAway.close()))
    )

    assert reading.name_parts == (ValueToken.of("ku"),)
    assert reading.name_breaks == (BrokenAway.close(),)
    assert reading.name == "ku"
    assert reading.value == "ku]"


def test_a_break_cannot_be_put_in_the_name_parts() -> None:
    mixed = cast(Sequence[ValueToken], (ValueToken.of("ku"), BrokenAway.close()))

    with pytest.raises(ValueError, match="belongs in name_breaks"):
        Reading.of_arguments(NamedSignArguments(mixed))


def test_converters_only_materialize_their_sequence() -> None:
    parts = (ValueToken.of("ku"),)
    breaks = (BrokenAway.open(),)

    assert convert_name_parts(list(parts)) == parts
    assert convert_name_breaks(list(breaks)) == breaks


def test_a_named_sign_serializes_the_two_arrays_separately() -> None:
    dumped = cast(Dict[str, Any], NamedSignSchema().dump(_broken_reading()))

    assert [part["value"] for part in dumped["nameParts"]] == ["k", "u"]
    assert [part["value"] for part in dumped["nameBreaks"]] == ["]"]
    assert all(part["type"] == "ValueToken" for part in dumped["nameParts"])
    assert all(part["type"] == "BrokenAway" for part in dumped["nameBreaks"])


def test_a_break_in_the_name_parts_is_rejected_on_load() -> None:
    dumped = cast(Dict[str, Any], NamedSignSchema().dump(_broken_reading()))
    dumped["nameParts"] = dumped["nameParts"] + dumped["nameBreaks"]

    from marshmallow import ValidationError

    with pytest.raises(ValidationError):
        NamedSignSchema().load(dumped)


def test_a_payload_that_is_not_a_mapping_is_left_to_marshmallow() -> None:
    schema = NamedSignSchema()

    assert schema.separate_legacy_name_parts(["not", "a", "mapping"]) == [
        "not",
        "a",
        "mapping",
    ]


def test_a_payload_without_name_parts_is_left_alone() -> None:
    schema = NamedSignSchema()
    payload = {"name": "ku"}

    assert schema.separate_legacy_name_parts(payload) == payload


def test_a_string_name_parts_is_left_to_marshmallow() -> None:
    schema = NamedSignSchema()

    assert schema.separate_legacy_name_parts({"nameParts": "ku"}) == {"nameParts": "ku"}


def test_a_legacy_interleaved_payload_is_separated_on_load() -> None:
    reading = _broken_reading()
    dumped = cast(Dict[str, Any], NamedSignSchema().dump(reading))
    legacy = {key: value for key, value in dumped.items() if key != "nameBreaks"}
    legacy["nameParts"] = [
        dumped["nameParts"][0],
        dumped["nameBreaks"][0],
        dumped["nameParts"][1],
    ]

    separated = NamedSignSchema().separate_legacy_name_parts(legacy)

    assert [part["value"] for part in separated["nameParts"]] == ["k", "u"]
    assert [part["value"] for part in separated["nameBreaks"]] == ["]"]


def test_a_legacy_document_loads_to_the_same_reading() -> None:
    reading = _broken_reading()
    dumped = cast(Dict[str, Any], ReadingSchema().dump(reading))
    legacy = {key: value for key, value in dumped.items() if key != "nameBreaks"}
    legacy["nameParts"] = [
        dumped["nameParts"][0],
        dumped["nameBreaks"][0],
        dumped["nameParts"][1],
    ]

    assert ReadingSchema().load(legacy) == reading


def test_a_payload_that_already_has_name_breaks_is_untouched() -> None:
    schema = NamedSignSchema()
    payload: Dict[str, Any] = {"nameParts": [], "nameBreaks": []}

    assert schema.separate_legacy_name_parts(payload) is payload


def test_with_name_replaces_both_arrays() -> None:
    reading = Reading.of_name("ku")
    parts = (ValueToken.of("n"), ValueToken.of("u"))
    breaks = (BrokenAway.open(),)

    updated = reading.with_name(parts, breaks)

    assert updated.name_parts == parts
    assert updated.name_breaks == breaks
    assert updated.name == "nu"
    assert updated.name_tokens == (parts[0], breaks[0], parts[1])


def test_with_sign_replaces_only_the_sign() -> None:
    reading = Reading.of_name("ku")
    sign = ValueToken.of("KU")

    updated = reading.with_sign(sign)

    assert updated.sign == sign
    assert updated.name_parts == reading.name_parts
    assert updated.name_breaks == reading.name_breaks
    assert reading.sign is None
