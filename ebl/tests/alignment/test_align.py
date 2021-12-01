from alignment.vocabulary import Vocabulary  # pyre-ignore[21]

from ebl.alignment.application.align import align, align_pair
from ebl.alignment.domain.sequence import NamedSequence
from ebl.alignment.domain.scoring import match


def test_align_pair() -> None:
    vocabulary = Vocabulary()
    sequence_1 = NamedSequence.of_signs("name1", "ABZ001", vocabulary)
    sequence_2 = NamedSequence.of_signs("name2", "ABZ001", vocabulary)

    result = align_pair(sequence_1, sequence_2, vocabulary)

    assert result.score == match
    assert result.a == sequence_1
    assert result.b == sequence_2
    assert len(result.alignments) == 1


def test_align() -> None:
    vocabulary = Vocabulary()
    sequence_1 = NamedSequence.of_signs("name1", "ABZ001", vocabulary)
    sequence_2 = NamedSequence.of_signs("name2", "ABZ001", vocabulary)
    sequence_3 = NamedSequence.of_signs("name3", "ABZ002", vocabulary)

    result = align([(sequence_1, sequence_3), (sequence_1, sequence_2)], vocabulary)

    assert result == "name1, name2, 16, 100.0, 100.0\nname1, name3, 0, 0.0, 0.0"