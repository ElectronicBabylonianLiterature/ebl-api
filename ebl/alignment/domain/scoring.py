from typing import Callable, Generator, Tuple
from alignment.sequencealigner import Scoring, GapScoring
from alignment.vocabulary import Vocabulary

from ebl.alignment.domain.sequence import UNCLEAR_OR_UNKNOWN_SIGN, LINE_BREAK
from ebl.transliteration.domain.atf import VARIANT_SEPARATOR

match = 16
mismatch = -5
common_mismatch = 7
break_match = 6
break_mismatch = -10
x_match = 3
x_mismatch = -3
gap_start = -5
gap_extension = -1
break_gap_extension = break_mismatch

curated_substitutions = frozenset(
    [
        frozenset(["ABZ545", "ABZ354"]),
        frozenset(["ABZ545", "ABZ597"]),
        frozenset(["ABZ411", "ABZ318"]),
        frozenset(["ABZ353", "ABZ597"]),
        frozenset(["ABZ207", "ABZ73"]),
        frozenset(["ABZ532", "ABZ427"]),
        frozenset(["ABZ68", "ABZ328"]),
        frozenset(["ABZ104", "ABZ7"]),
        frozenset(["ABZ427", "ABZ61"]),
        frozenset(["ABZ537", "ABZ55"]),
        frozenset(["ABZ586", "ABZ84"]),
        frozenset(["ABZ352", "ABZ138"]),
        frozenset(["ABZ367", "ABZ449"]),
        frozenset(["ABZ214", "ABZ371"]),
        frozenset(["ABZ308", "ABZ142"]),
        frozenset(["ABZ58", "ABZ73"]),
        frozenset(["ABZ231", "ABZ75"]),
        frozenset(["ABZ139", "ABZ73"]),
        frozenset(["ABZ342", "ABZ61"]),
        frozenset(["ABZ376", "ABZ73"]),
        frozenset(["ABZ579", "ABZ142"]),
        frozenset(["ABZ55", "ABZ59"]),
        frozenset(["ABZ381", "ABZ207"]),
        frozenset(["ABZ312", "ABZ75"]),
        frozenset(["ABZ371", "ABZ5"]),
        frozenset(["ABZ139", "ABZ207"]),
        frozenset(["ABZ328", "ABZ86"]),
        frozenset(["ABZ68", "ABZ86"]),
        frozenset(["ABZ75", "ABZ70"]),
        frozenset(["ABZ318", "ABZ142"]),
        frozenset(["ABZ139", "ABZ58"]),
        frozenset(["ABZ461", "ABZ536"]),
    ]
)


def is_curated(first_sign: str, second_sign: str) -> bool:
    return frozenset([first_sign, second_sign]) in curated_substitutions


def is_variant(first_decoded: str, second_decoded: str) -> bool:
    return VARIANT_SEPARATOR in first_decoded or VARIANT_SEPARATOR in second_decoded


class EblScoring(GapScoring, Scoring):
    def __init__(self, vocabulary: Vocabulary):
        self.vocabulary = vocabulary
        self.line_break = vocabulary.encode(LINE_BREAK)
        self.x = vocabulary.encode(UNCLEAR_OR_UNKNOWN_SIGN)

    def __call__(self, firstElement, secondElement) -> int:
        return next(
            score()
            for (predicate, score) in self._get_scores(firstElement, secondElement)
            if predicate
        )

    def gapStart(self, element) -> int:
        return gap_start

    def gapExtension(self, element) -> int:
        return break_gap_extension if element == self.line_break else gap_extension

    def _get_scores(
        self, firstElement, secondElement
    ) -> Generator[Tuple[bool, Callable[[], int]], None, None]:
        first_decoded = self.vocabulary.decode(firstElement)
        second_decoded = self.vocabulary.decode(secondElement)

        yield (
            self._is_break(firstElement, secondElement),
            lambda: self._get_break_score(firstElement, secondElement),
        )
        yield (
            self._is_x(firstElement, secondElement),
            lambda: self._get_x_score(firstElement, secondElement),
        )
        yield (is_curated(first_decoded, second_decoded), lambda: common_mismatch)
        yield (
            is_variant(first_decoded, second_decoded),
            lambda: self._get_variant_score(first_decoded, second_decoded),
        )
        yield (True, lambda: match if firstElement == secondElement else mismatch)

    def _is_break(self, first_element, second_element) -> bool:
        return first_element == self.line_break or second_element == self.line_break

    def _is_x(self, first_element, second_element) -> bool:
        return first_element == self.x or second_element == self.x

    def _get_break_score(self, first_element, second_element) -> int:
        return break_match if first_element == second_element else break_mismatch

    def _get_x_score(self, first_element, second_element) -> int:
        return x_match if first_element == second_element else x_mismatch

    def _get_variant_score(self, first_decoded: str, second_decoded: str) -> int:
        result = []
        for first_part in first_decoded.split(VARIANT_SEPARATOR):
            for second_part in second_decoded.split(VARIANT_SEPARATOR):
                result.append(
                    self(
                        self.vocabulary.encode(first_part),
                        self.vocabulary.encode(second_part),
                    )
                )
        return max(result)
