from ebl.fragmentarium.domain.date import (
    DateKing,
    DateEponymSchema,
    DateSchema,
    Year,
    YearSchema,
    MonthSchema,
    DaySchema,
)


def test_labeled_schema():
    year_param = YearSchema().load({"value": "10", "isBroken": True})
    month_param = MonthSchema().load({"value": "5", "isIntercalary": True})
    day_param = DaySchema().load({"value": "1", "isUncertain": True})

    assert YearSchema().dump(year_param) == {
        "value": "10",
        "isBroken": True,
    }
    assert MonthSchema().dump(month_param) == {
        "value": "5",
        "isIntercalary": True,
    }
    assert DaySchema().dump(day_param) == {
        "value": "1",
        "isUncertain": True,
    }


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
    assert year == Year(value="5", is_reconstructed=True)
    assert YearSchema().dump(year) == {"value": "5", "isReconstructed": True}


def test_year_schema_parse_broken():
    year = YearSchema().load({"value": "[5]"})
    assert year == Year(value="5", is_broken=True)
    assert YearSchema().dump(year) == {"value": "5", "isBroken": True}


def test_year_schema_parse_uncertain_parens():
    year = YearSchema().load({"value": "(5)"})
    assert year == Year(value="5", is_uncertain=True)
    assert YearSchema().dump(year) == {"value": "5", "isUncertain": True}


def test_year_schema_parse_emended():
    year = YearSchema().load({"value": "5!"})
    assert year == Year(value="5", is_emended=True)
    assert YearSchema().dump(year) == {"value": "5", "isEmended": True}


def test_year_schema_parse_uncertain_question_mark():
    year = YearSchema().load({"value": "5?"})
    assert year == Year(value="5", is_uncertain=True)
    assert YearSchema().dump(year) == {"value": "5", "isUncertain": True}


def test_year_schema_parse_no_wrapper():
    year = YearSchema().load({"value": "5"})
    assert year == Year(value="5")
    assert YearSchema().dump(year) == {"value": "5"}


def test_year_schema_structured_metadata_takes_priority_over_wrapper():
    year = YearSchema().load({"value": "<5>", "isReconstructed": False})
    assert year.value == "5"
    assert year.is_reconstructed is False


def test_date_king_king_property_found():
    date_king = DateKing(order_global=1)
    assert date_king.king is not None


def test_date_king_king_property_not_found():
    date_king = DateKing(order_global=99999)
    assert date_king.king is None


def test_date_eponym_schema_round_trip():
    data = {"phase": "Neo-Assyrian", "isBroken": True, "isUncertain": False}
    eponym = DateEponymSchema().load(data)
    assert eponym.is_broken is True
    assert eponym.is_uncertain is False


def test_date_schema():
    date_input = {
        "year": {"value": "2300"},
        "month": {"value": "5"},
        "day": {"value": "1"},
        "king": {
            "orderGlobal": 1,
        },
        "ur3Calendar": "Nippur",
    }
    DateSchema().load(date_input)
    serialized_date = DateSchema().dump(DateSchema().load(date_input))
    assert date_input == serialized_date
