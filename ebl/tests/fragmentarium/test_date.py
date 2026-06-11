from ebl.fragmentarium.domain.date import (
    DateKing,
    DateEponymSchema,
    DateSchema,
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


def test_month_schema_excludes_year_only_fields():
    month = MonthSchema().load(
        {"value": "5", "isReconstructed": True, "isEmended": True}
    )
    assert not hasattr(month, "is_reconstructed")
    assert not hasattr(month, "is_emended")


def test_day_schema_excludes_year_only_fields():
    day = DaySchema().load({"value": "1", "isReconstructed": True, "isEmended": True})
    assert not hasattr(day, "is_reconstructed")
    assert not hasattr(day, "is_emended")


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
