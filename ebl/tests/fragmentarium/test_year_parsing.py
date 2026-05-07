from ebl.fragmentarium.domain.date import (
    DateSchema,
    Year,
    YearSchema,
)


def test_year_schema_new_fields():
    year = YearSchema().load({"value": "5", "isReconstructed": True, "isEmended": True})
    assert year == Year(value="5", is_reconstructed=True, is_emended=True)
    assert YearSchema().dump(year) == {
        "value": "5",
        "isReconstructed": True,
        "isEmended": True,
    }


def test_year_schema_parse_reconstructed():
    year = YearSchema().load({"value": "<5>"})
    assert year == Year(value="5", is_reconstructed=True, original_value="<5>")
    assert YearSchema().dump(year) == {
        "value": "5",
        "isReconstructed": True,
        "originalValue": "<5>",
    }


def test_year_schema_parse_broken():
    year = YearSchema().load({"value": "[5]"})
    assert year == Year(value="5", is_broken=True, original_value="[5]")
    assert YearSchema().dump(year) == {
        "value": "5",
        "isBroken": True,
        "originalValue": "[5]",
    }


def test_year_schema_parse_uncertain_parens():
    year = YearSchema().load({"value": "(5)"})
    assert year == Year(value="5", is_uncertain=True, original_value="(5)")
    assert YearSchema().dump(year) == {
        "value": "5",
        "isUncertain": True,
        "originalValue": "(5)",
    }


def test_year_schema_parse_emended():
    year = YearSchema().load({"value": "5!"})
    assert year == Year(value="5", is_emended=True, original_value="5!")
    assert YearSchema().dump(year) == {
        "value": "5",
        "isEmended": True,
        "originalValue": "5!",
    }


def test_year_schema_parse_uncertain_question_mark():
    year = YearSchema().load({"value": "5?"})
    assert year == Year(value="5", is_uncertain=True, original_value="5?")
    assert YearSchema().dump(year) == {
        "value": "5",
        "isUncertain": True,
        "originalValue": "5?",
    }


def test_year_schema_parse_no_wrapper():
    year = YearSchema().load({"value": "5"})
    assert year == Year(value="5")
    assert YearSchema().dump(year) == {"value": "5"}


def test_year_schema_explicit_true_flag_preserves_value():
    year = YearSchema().load({"value": "<5>", "isReconstructed": True})
    assert year.value == "<5>"
    assert year.is_reconstructed is True
    assert year.original_value is None


def test_year_schema_explicit_false_flag_preserves_value():
    year = YearSchema().load({"value": "<5>", "isReconstructed": False})
    assert year.value == "<5>"
    assert year.is_reconstructed is False
    assert year.original_value is None


def test_year_schema_explicit_trailing_marker_flag_preserves_value():
    year = YearSchema().load({"value": "5!", "isEmended": True})
    assert year.value == "5!"
    assert year.is_emended is True
    assert year.original_value is None


def test_year_schema_parse_mixed_reconstructed_uncertain():
    year = YearSchema().load({"value": "<5>?"})
    assert year == Year(
        value="5", is_reconstructed=True, is_uncertain=True, original_value="<5>?"
    )


def test_year_schema_parse_mixed_reconstructed_emended():
    year = YearSchema().load({"value": "<5>!"})
    assert year == Year(
        value="5", is_reconstructed=True, is_emended=True, original_value="<5>!"
    )


def test_year_schema_parse_mixed_broken_uncertain():
    year = YearSchema().load({"value": "[5]?"})
    assert year == Year(
        value="5", is_broken=True, is_uncertain=True, original_value="[5]?"
    )


def test_year_schema_parse_mixed_broken_emended():
    year = YearSchema().load({"value": "[5]!"})
    assert year == Year(
        value="5", is_broken=True, is_emended=True, original_value="[5]!"
    )


def test_year_schema_parse_mixed_uncertain_paren_emended():
    year = YearSchema().load({"value": "(5)!"})
    assert year == Year(
        value="5", is_uncertain=True, is_emended=True, original_value="(5)!"
    )


def test_year_schema_parse_nested_layers():
    year = YearSchema().load({"value": "[(5!)]?"})
    assert year == Year(
        value="5",
        is_broken=True,
        is_uncertain=True,
        is_emended=True,
        original_value="[(5!)]?",
    )


def test_year_schema_parse_nested_alt_order():
    year = YearSchema().load({"value": "([5?])!"})
    assert year == Year(
        value="5",
        is_uncertain=True,
        is_broken=True,
        is_emended=True,
        original_value="([5?])!",
    )


def test_year_schema_parse_triple_wrapper():
    year = YearSchema().load({"value": "[<(5)>]"})
    assert year == Year(
        value="5",
        is_broken=True,
        is_reconstructed=True,
        is_uncertain=True,
        original_value="[<(5)>]",
    )


def test_year_schema_parse_idempotent_double_wrapper():
    year = YearSchema().load({"value": "<<5>>"})
    assert year == Year(value="5", is_reconstructed=True, original_value="<<5>>")


def test_year_schema_parse_degenerate_wrappers_left_alone():
    for raw in ["<>", "[]", "()", "!", "?", ""]:
        year = YearSchema().load({"value": raw})
        assert year.value == raw
        assert year.is_broken is None
        assert year.is_uncertain is None
        assert year.is_reconstructed is None
        assert year.is_emended is None
        assert year.original_value is None


def test_year_schema_missing_value_defaults_to_empty():
    year = YearSchema().load({})
    assert year == Year(value="")


def test_year_schema_does_not_mutate_input():
    payload = {"value": "<5>?"}
    YearSchema().load(payload)
    assert payload == {"value": "<5>?"}


def test_year_schema_original_value_round_trip():
    year = YearSchema().load({"value": "<5>"})
    dumped = YearSchema().dump(year)
    assert dumped == {"value": "5", "isReconstructed": True, "originalValue": "<5>"}
    reloaded = YearSchema().load(dumped)
    assert reloaded == year


def test_year_schema_explicit_original_value_preserved():
    year = YearSchema().load(
        {"value": "5", "isReconstructed": True, "originalValue": "<5>"}
    )
    assert year.original_value == "<5>"


def test_date_schema_legacy_db_value_round_trip_preserves_original():
    legacy_db_payload = {
        "year": {"value": "<5>"},
        "month": {"value": "5"},
        "day": {"value": "1"},
        "ur3Calendar": "Nippur",
    }
    parsed = DateSchema().load(legacy_db_payload)
    assert parsed.year.value == "5"
    assert parsed.year.is_reconstructed is True
    assert parsed.year.original_value == "<5>"
    dumped = DateSchema().dump(parsed)
    assert dumped["year"]["originalValue"] == "<5>"
    assert dumped["year"]["value"] == "5"
    assert DateSchema().load(dumped) == parsed
