import pytest
import re
from ebl.transliteration.domain.stage import Stage, ABBREVIATIONS


def test_abbreviation_completeness() -> None:
    assert set(ABBREVIATIONS) == set(Stage)


@pytest.mark.parametrize("stage", Stage)
def test_slug(stage: Stage) -> None:
    allowed_slug_chars = re.compile(r"^[a-zA-Z0-9_\s-]+$")
    long_name = stage.value
    abbreviation = ABBREVIATIONS[stage]

    assert allowed_slug_chars.match(long_name)
    assert allowed_slug_chars.match(abbreviation)
