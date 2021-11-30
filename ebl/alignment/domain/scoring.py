from alignment.sequencealigner import Scoring, GapScoring  # pyre-ignore[21]
from alignment.vocabulary import Vocabulary  # pyre-ignore[21]


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


class EblScoring(GapScoring, Scoring):  # pyre-ignore[11]
    def __init__(self, vocabulary: Vocabulary):  # pyre-ignore[11]
        self.vocabulary = vocabulary
        self.line_break = vocabulary.encode("#")
        self.x = vocabulary.encode("X")

    def __call__(self, firstElement, secondElement) -> int:
        first_decoded = self.vocabulary.decode(firstElement)
        second_decoded = self.vocabulary.decode(secondElement)

        if firstElement == self.line_break or secondElement == self.line_break:
            return break_match if firstElement == secondElement else break_mismatch
        elif firstElement == self.x or secondElement == self.x:
            return x_match if firstElement == secondElement else x_mismatch
        elif frozenset([first_decoded, second_decoded]) in curated_substitutions:
            return common_mismatch
        elif "/" in first_decoded or "/" in second_decoded:
            result = []
            for first_part in first_decoded.split("/"):
                for second_part in second_decoded.split("/"):
                    result.append(
                        self(
                            self.vocabulary.encode(first_part),
                            self.vocabulary.encode(second_part),
                        )
                    )
            return max(result)
        elif firstElement == secondElement:
            return match
        else:
            return mismatch

    def gapStart(self, element) -> int:
        return gap_start

    def gapExtension(self, element) -> int:
        return break_gap_extension if element == self.line_break else gap_extension
