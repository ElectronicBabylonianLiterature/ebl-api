import pytest

from ebl.corpus.domain.text_id import TextId


@pytest.mark.parametrize(
    "text_id,expected", [(TextId(0, 0), "0.0"), (TextId(5, 8), "V.8")]
)
def test_str(text_id, expected) -> None:
    assert str(text_id) == expected
