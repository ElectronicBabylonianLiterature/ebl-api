from alignment.vocabulary import Vocabulary
from hamcrest import assert_that, has_properties, contains_exactly

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

    assert_that(
        result,
        contains_exactly(has_properties({"score": 16}), has_properties({"score": 0})),
    )
