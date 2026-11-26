import pytest

from ebl.tests.factories.corpus import TextFactory
from ebl.tests.factories.ids import TextIdFactory

SEQUENCES = [(4999, 4999), (5000, 0), (12345, 2345)]


@pytest.mark.parametrize("sequence,category", SEQUENCES)
def test_category_stays_in_roman_numeral_range(sequence: int, category: int) -> None:
    text_id = TextIdFactory.build(__sequence=sequence)

    assert text_id.category == category
    assert text_id.index == sequence
    assert str(text_id).endswith(f".{sequence}")


@pytest.mark.parametrize("sequence,category", SEQUENCES)
def test_text_category_stays_in_roman_numeral_range(
    sequence: int, category: int
) -> None:
    text = TextFactory.build(__sequence=sequence)

    assert text.category == category
    assert text.index == sequence
    assert str(text.id).endswith(f".{sequence}")
