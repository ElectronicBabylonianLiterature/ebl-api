import pytest

from ebl.transliteration.domain.sign_tokens import Reading


def test_named_sign_accepts_a_non_negative_sub_index() -> None:
    assert Reading.of_name("ku", 0).sub_index == 0


def test_named_sign_accepts_an_absent_sub_index() -> None:
    assert Reading.of_name("ku", None).sub_index is None


def test_named_sign_rejects_a_negative_sub_index() -> None:
    with pytest.raises(ValueError, match="Sub-index must be >= 0."):
        Reading.of_name("ku", -1)
