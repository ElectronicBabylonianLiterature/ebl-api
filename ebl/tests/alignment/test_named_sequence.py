from alignment.sequence import Sequence
from alignment.vocabulary import Vocabulary
from ebl.alignment.domain.sequence import NamedSequence
from ebl.tests.factories.fragment import FragmentFactory

signs = "X X ABZ001\nABZ002\nX X X\n"
ocred_signs = ""
sequence = Sequence(["ABZ001", "#", "ABZ002", "#", "#"])


def test_of_signs() -> None:
    vocabulary = Vocabulary()
    name = 1234
    named = NamedSequence.of_signs(name, signs, vocabulary)

    assert named.name == str(name)
    assert named.sequence == vocabulary.encodeSequence(sequence)


def test_of_fragment() -> None:
    vocabulary = Vocabulary()
    fragment = FragmentFactory.build(signs=signs, ocred_signs=ocred_signs)
    named = NamedSequence.of_fragment(fragment, vocabulary)

    assert named.name == str(fragment.number)
    assert named.sequence == vocabulary.encodeSequence(sequence)
