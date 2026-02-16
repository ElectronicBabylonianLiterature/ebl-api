from hamcrest import assert_that, has_properties
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.fragmentarium.domain.joins import Join, Joins
from hamcrest.library import contains_exactly
from hamcrest.core.core.isequal import equal_to


def test_join() -> None:
    museum_number = MuseumNumber("X", "1")
    is_checked = True
    is_envelope = True
    joined_by = "Test User"
    date = "today"
    note = "test join"
    legacy_data = "old stuff"

    join = Join(
        museum_number, is_checked, is_envelope, joined_by, date, note, legacy_data
    )

    assert_that(
        join,
        has_properties(
            {
                "museum_number": museum_number,
                "is_checked": is_checked,
                "is_envelope": is_envelope,
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
        "is_envelope": False,
        "joined_by": "",
        "date": "",
        "note": "",
        "legacy_data": "",
    }

    join = Join(MuseumNumber("X", "1"))

    assert_that(join, has_properties(defaults))


def test_joins_fragments_sorting():
    joins = Joins(
        (
            (Join(MuseumNumber("B", "2")), Join(MuseumNumber("B", "1"))),
            (Join(MuseumNumber("Z", "0")), Join(MuseumNumber("A", "3"))),
        )
    )

    assert_that(
        joins.fragments,
        contains_exactly(
            contains_exactly(
                Join(MuseumNumber("A", "3")), Join(MuseumNumber("Z", "0"))
            ),
            contains_exactly(
                Join(MuseumNumber("B", "1")), Join(MuseumNumber("B", "2"))
            ),
        ),
    )


def test_joins_lowest():
    joins = Joins(
        (
            (Join(MuseumNumber("B", "2"), is_in_fragmentarium=True),),
            (
                Join(MuseumNumber("B", "1"), is_in_fragmentarium=True),
                Join(MuseumNumber("A", "1"), is_in_fragmentarium=False),
            ),
        )
    )

    assert_that(joins.lowest, equal_to(MuseumNumber("B", "1")))


def test_joins_lowest_when_no_fragments():
    assert_that(Joins().lowest, equal_to(None))
