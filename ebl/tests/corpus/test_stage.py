import pytest
import re
from ebl.transliteration.domain.stage import Stage

VALUES = [
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
    ("Uruk IV", "Uruk4"),
    ("Uruk III-Jemdet Nasr", "JN"),
    ("ED I-II", "ED1-2"),
    ("Fara", "Fara"),
    ("Presargonic", "PSarg"),
    ("Sargonic", "Sarg"),
]


@pytest.mark.parametrize(
    "value,abbreviation",
    VALUES,
)
def test_abbreviation(value, abbreviation) -> None:
    assert Stage(value).abbreviation == abbreviation


@pytest.mark.parametrize("item", VALUES)
def test_slug(item) -> None:
    allowed_slug_chars = re.compile(r"^[a-zA-Z0-9-\s]+$")
    long_name, abbreviation = item

    assert allowed_slug_chars.match(long_name)
    assert allowed_slug_chars.match(abbreviation)
