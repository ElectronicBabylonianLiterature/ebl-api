from typing import Any, Dict, cast

from ebl.chronology.chronology import Eponym, EponymSchema, King, KingSchema

KING_PAYLOAD = {
    "orderGlobal": 1.0,
    "groupWith": None,
    "dynastyNumber": "1",
    "dynastyName": "First Dynasty of Babylon",
    "orderInDynasty": "1",
    "name": "Sumu-abum",
    "date": "1894-1881",
    "totalOfYears": "14",
    "notes": None,
    "isNotInBrinkman": None,
}

EPONYM_PAYLOAD = {
    "date": "910",
    "name": "Adad-nerari",
    "title": "king",
    "area": "Assur",
    "event": "accession",
    "phase": "NA",
    "notes": None,
    "king": None,
    "isKing": None,
    "rel": None,
}


def _dump_king(payload: Dict[str, Any]) -> Dict[str, Any]:
    return cast(Dict[str, Any], KingSchema().dump(KingSchema().load(payload)))


def _dump_eponym(payload: Dict[str, Any]) -> Dict[str, Any]:
    return cast(Dict[str, Any], EponymSchema().dump(EponymSchema().load(payload)))


def test_a_king_loads_into_the_domain_object() -> None:
    king = KingSchema().load(KING_PAYLOAD)

    assert isinstance(king, King)
    assert king.name == "Sumu-abum"
    assert king.notes is None


def test_dumping_a_king_drops_every_none_field() -> None:
    dumped = _dump_king(KING_PAYLOAD)

    assert "notes" not in dumped
    assert "groupWith" not in dumped
    assert "isNotInBrinkman" not in dumped
    assert dumped["name"] == "Sumu-abum"


def test_dumping_a_king_keeps_every_populated_field() -> None:
    dumped = _dump_king({**KING_PAYLOAD, "notes": "a note", "groupWith": 2})

    assert dumped["notes"] == "a note"
    assert dumped["groupWith"] == 2


def test_an_eponym_loads_into_the_domain_object() -> None:
    eponym = EponymSchema().load(EPONYM_PAYLOAD)

    assert isinstance(eponym, Eponym)
    assert eponym.name == "Adad-nerari"
    assert eponym.rel is None


def test_dumping_an_eponym_drops_every_none_field() -> None:
    dumped = _dump_eponym(EPONYM_PAYLOAD)

    assert "notes" not in dumped
    assert "king" not in dumped
    assert "rel" not in dumped
    assert dumped["name"] == "Adad-nerari"


def test_dumping_an_eponym_keeps_every_populated_field() -> None:
    dumped = _dump_eponym({**EPONYM_PAYLOAD, "king": "Assur", "rel": 3})

    assert dumped["king"] == "Assur"
    assert dumped["rel"] == 3
