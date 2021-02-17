import pytest

from ebl.corpus.domain.stage import Stage


@pytest.mark.parametrize(
    "value,abbreviation",
    [
        ("Ur III", "Ur3"),
        ("Old Assyrian", "OA"),
        ("Old Babylonian", "OB"),
        ("Middle Babylonian", "MB"),
        ("Middle Assyrian", "MA"),
        ("Hittite", "Hit"),
        ("Neo-Assyrian", "NA"),
        ("Neo-Babylonian", "NB"),
        ("Late Babylonian", "LB"),
        ("Persian", "Per"),
        ("Hellenistic", "Hel"),
        ("Parthian", "Par"),
        ("Uncertain", "Unc"),
        ("Standard Babylonian", "SB"),
    ],
)
def test_abbreviation(value, abbreviation) -> None:
    assert Stage(value).abbreviation == abbreviation
