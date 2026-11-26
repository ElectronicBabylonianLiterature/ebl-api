from datetime import date

from ebl.fragmentarium.application.date_schemas import IsoDateField


def test_iso_date_field_accepts_base_serialization_keywords() -> None:
    field = IsoDateField()

    assert (
        field._serialize(value=date(2026, 10, 21), attr=None, obj=None) == "2026-10-21"
    )


def test_iso_date_field_accepts_base_deserialization_keywords() -> None:
    field = IsoDateField()

    assert field._deserialize(value="2026-10-21", attr=None, data={}) == date(
        2026, 10, 21
    )
