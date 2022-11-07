import pytest
from ebl.fragmentarium.infrastructure.phrase_matcher import PhraseMatcher


LEMMA_LINES = [
    [["line"], ["with", "a"], ["phrase"], ["to"], ["match"]],
    [["another", "line"], ["with"], [], ["empty"], ["lemmas"], []],
    [["short"], ["line"]],
    [["longer"], ["short"], ["line"]],
]


def get_matches(phrase):
    matcher = PhraseMatcher(phrase)
    return [i for i, line in enumerate(LEMMA_LINES) if matcher.matches(line)]


@pytest.mark.parametrize(
    "phrase,expected",
    [
        (["phrase", "to", "match"], [0]),
        (["line", "with", "a"], []),
        (["line", "with", "", "empty"], [1]),
        (["too", "short", "line"], []),
        (["line", ""], []),
        (["line"], [0, 1, 2, 3]),
    ],
)
def test_phrase_matcher(phrase, expected):
    assert get_matches(phrase) == expected
