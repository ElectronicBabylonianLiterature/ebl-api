from hamcrest import assert_that, has_properties
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.fragmentarium.domain.joins import Join


def test_join() -> None:
    museum_number = MuseumNumber("X", "1")
    is_checked = True
    joined_by = "Test User"
    date = "today"
    note = "test join"
    legacy_data = "old stuff"

    join = Join(museum_number, is_checked, joined_by, date, note, legacy_data)

    assert_that(
        join,
        has_properties(
            {
                "museum_number": museum_number,
                "is_checked": is_checked,
                "joined_by": joined_by,
                "date": date,
                "note": note,
                "legacy_data": legacy_data,
            }
        ),
    )


def test_join_default() -> None:
    defaults = {
        "is_checked": False,
        "joined_by": "",
        "date": "",
        "note": "",
        "legacy_data": "",
    }

    join = Join(MuseumNumber("X", "1"))

    assert_that(join, has_properties(defaults))
