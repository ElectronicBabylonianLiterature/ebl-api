from alignment.vocabulary import Vocabulary

from ebl.alignment.domain.result import AlignmentResult
from ebl.alignment.domain.sequence import NamedSequence


def test_alignment_result() -> None:
    vocabulary = Vocabulary()
    sequence_1 = NamedSequence.of_signs("name1", "ABZ001", vocabulary)
    sequence_2 = NamedSequence.of_signs("name2", "ABZ002", vocabulary)
    score = 10
    alignments = []
    result = AlignmentResult(score, sequence_1, sequence_2, alignments)

    assert result.score == score
    assert result.a == sequence_1
    assert result.b == sequence_2
    assert result.alignments == alignments
