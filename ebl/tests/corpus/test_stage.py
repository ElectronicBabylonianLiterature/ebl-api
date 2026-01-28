import pytest
import re
from ebl.common.domain.stage import Stage


@pytest.mark.parametrize("stage", Stage)
def test_slug(stage: Stage) -> None:
    allowed_slug_chars = re.compile(r"^[a-zA-Z0-9_\s-]+$")
    assert allowed_slug_chars.match(stage.long_name)
    assert allowed_slug_chars.match(stage.abbreviation)
