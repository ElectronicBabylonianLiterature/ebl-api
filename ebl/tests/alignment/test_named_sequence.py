from alignment.sequence import Sequence  # pyre-ignore[21]
from alignment.vocabulary import Vocabulary  # pyre-ignore[21]
from ebl.alignment.domain.sequence import NamedSequence


def test_of_signs() -> None:
    vocabulary = Vocabulary()
    name = 1234
    named = NamedSequence.of_signs(name, "X X ABZ001\nABZ002\nX X X\n", vocabulary)

    assert named.name == str(name)
    assert named.sequence == vocabulary.encodeSequence(
        Sequence(["ABZ001", "#", "ABZ002", "#", "#"])
    )
