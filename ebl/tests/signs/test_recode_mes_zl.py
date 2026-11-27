import pytest

from ebl.signs.infrastructure.sign_schemas import COLLECTION
from ebl.signs.recode_mes_zl import (
    RECODINGS,
    ROTATED_GIR3,
    Recoding,
    recode_text,
    run_recoding,
)

GIR3 = (
    "701\t**GÌR** 𒄊\n"
    f"Siehe auch Kap. II. {ROTATED_GIR3} siehe Kap. II.\n"
    "𒄊𒁄 = GÌR-BAL = *riḫṣu*."
)
ESE3 = (
    "114\t**ÈŠE**\t𒑘\nZu altakk. AŠ+U = 600 und 𒀸𒐴 (AŠ+Ugunû) = 6000^?^ siehe Kap. II."
)
RECODING = Recoding("1", ("A", "B"), "x 𒀸 y", "x 􀀁 y", "test")


@pytest.fixture
def signs(database):
    collection = database[COLLECTION]
    collection.insert_many(
        [
            {"_id": "GIR₃", "mesZl": GIR3},
            {"_id": "PIRIG", "mesZl": GIR3},
            {"_id": "EŠE₃", "mesZl": ESE3},
        ]
    )
    return collection


def test_recode_text_replaces_the_single_passage() -> None:
    assert recode_text("a x 𒀸 y b", RECODING) == "a x 􀀁 y b"


@pytest.mark.parametrize("text", ["a b", "x 𒀸 y x 𒀸 y"])
def test_recode_text_needs_exactly_one_passage(text: str) -> None:
    assert recode_text(text, RECODING) is None


def test_every_recoding_changes_its_passage() -> None:
    for recoding in RECODINGS:
        assert recoding.old != recoding.new
        assert recode_text(f"…{recoding.old}…", recoding) == f"…{recoding.new}…"


def test_rotated_gir3_becomes_the_inversum_sign(signs) -> None:
    run_recoding(signs)
    for sign in ("GIR₃", "PIRIG"):
        text = signs.find_one({"_id": sign})["mesZl"]
        assert "rotate" not in text
        assert "Siehe auch Kap. II. \U001000c8 siehe Kap. II." in text
        assert "𒄊𒁄 = GÌR-BAL" in text


def test_ese3_gets_the_single_sign(signs) -> None:
    run_recoding(signs)
    assert "\U001000c3 (AŠ+Ugunû)" in signs.find_one({"_id": "EŠE₃"})["mesZl"]


def test_report(signs) -> None:
    statuses = {
        (result.recoding.mes_zl, result.sign): result.status
        for result in run_recoding(signs)
    }
    assert statuses[("701c", "GIR₃")] == "recoded"
    assert statuses[("114a", "EŠE₃")] == "recoded"
    assert statuses[("298v", "DUH")] == "no sign"

    again = {
        (result.recoding.mes_zl, result.sign): result.status
        for result in run_recoding(signs)
    }
    assert again[("701c", "GIR₃")] == "already recoded"
    assert again[("114a", "EŠE₃")] == "already recoded"


def test_dry_run_changes_nothing(signs) -> None:
    results = run_recoding(signs, dry_run=True)
    assert any(result.status == "recoded" for result in results)
    assert signs.find_one({"_id": "GIR₃"})["mesZl"] == GIR3
    assert signs.find_one({"_id": "EŠE₃"})["mesZl"] == ESE3


def test_passage_not_found(signs) -> None:
    signs.insert_one({"_id": "X", "mesZl": "nothing to see"})
    results = run_recoding(signs, [Recoding("1", ("X",), "a𒀸", "b", "test")])
    assert [result.status for result in results] == ["passage not found"]
