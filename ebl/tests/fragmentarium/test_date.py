from ebl.fragmentarium.domain.date import (
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
