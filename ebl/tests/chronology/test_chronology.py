import json
from ebl.chronology.chronology import KingSchema, ChronologySchema, Chronology, King


def test_king_creation():
    king = King(
        1, 2, "dyn1", "Dynasty 1", "1", "King A", "1999", "10 years", "Some notes", None
    )

    assert king.order_global == 1
    assert king.group_with == 2
    assert king.dynasty_number == "dyn1"
    assert king.dynasty_name == "Dynasty 1"
    assert king.order_in_dynasty == "1"
    assert king.name == "King A"
    assert king.date == "1999"
    assert king.total_of_years == "10 years"
    assert king.notes == "Some notes"


def test_chronology_creation():
    king_a = King(
        1, 2, "dyn1", "Dynasty 1", "1", "King A", "1999", "10 years", "Some notes", None
    )
    king_b = King(
        2, 2, "dyn2", "Dynasty 2", "2", "King B", "2000", "5 years", "Other notes", True
    )
    chronology = Chronology([king_a, king_b])

    assert chronology.kings == [king_a, king_b]


def test_find_king_by_name():
    king_a = King(
        1, 2, "dyn1", "Dynasty 1", "1", "King A", "1999", "10 years", "Some notes", None
    )
    king_b = King(
        2, 2, "dyn2", "Dynasty 2", "2", "King B", "2000", "5 years", "Other notes", True
    )
    chronology = Chronology([king_a, king_b])

    assert chronology.find_king_by_name("King A") == king_a
    assert chronology.find_king_by_name("King B") == king_b
    assert chronology.find_king_by_name("King C") is None


def test_king_schema_deserialization():
    king_data = {
        "orderGlobal": 1,
        "groupWith": 2,
        "dynastyNumber": "dyn1",
        "dynastyName": "Dynasty 1",
        "orderInDynasty": "1",
        "name": "King A",
        "date": "1999",
        "totalOfYears": "10 years",
        "notes": "Some notes",
    }
    king = KingSchema().load(king_data)

    assert king.order_global == 1
    assert king.group_with == 2
    assert king.dynasty_number == "dyn1"
    assert king.dynasty_name == "Dynasty 1"
    assert king.order_in_dynasty == "1"
    assert king.name == "King A"
    assert king.date == "1999"
    assert king.total_of_years == "10 years"
    assert king.notes == "Some notes"


def test_chronology_schema_deserialization():
    with open("ebl/chronology/brinkmanKings.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        chronology = ChronologySchema().load({"kings": data})
    assert len(chronology.kings) == 400
    assert chronology.kings[0].name == "Sargon"
    assert chronology.kings[-2].name == "Sin-šar-iškun"
