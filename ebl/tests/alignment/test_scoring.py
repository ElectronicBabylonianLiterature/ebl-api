from alignment.vocabulary import Vocabulary
import pytest

from ebl.alignment.domain.scoring import EblScoring


@pytest.mark.parametrize(
    "first,second,expected",
    [
        ("ABZ001", "ABZ001", 16),
        ("ABZ001", "ABZ002", -5),
        ("ABZ545", "ABZ597", 7),
        ("#", "#", 6),
        ("#", "ABZ002", -10),
        ("X", "X", 3),
        ("ABZ001", "X", -3),
        ("ABZ001/ABZ545/ABZ002", "ABZ003/ABZ545/ABZ001", 16),
        ("ABZ545/ABZ002", "ABZ003/ABZ597", 7),
        ("ABZ001/ABZ002", "ABZ003/ABZ004", -5),
    ],
)
def test_scoring(first, second, expected) -> None:
    vocabulary = Vocabulary()
    first = vocabulary.encode(first)
    second = vocabulary.encode(second)

    assert EblScoring(vocabulary)(first, second) == expected


def test_gap_start() -> None:
    vocabulary = Vocabulary()
    assert EblScoring(vocabulary).gapStart(vocabulary.encode("ABZ001")) == -5


@pytest.mark.parametrize("element,expected", [("ABZ001", -1), ("#", -10)])
def test_gap_xtension(element, expected) -> None:
    vocabulary = Vocabulary()
    assert EblScoring(vocabulary).gapExtension(vocabulary.encode(element)) == expected
