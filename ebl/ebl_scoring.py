from alignment.sequencealigner import Scoring
from alignment.vocabulary import Vocabulary

match = 2
mismatch = -1
commonMismatch = 1
breakMatch = 2
breakMismatch = -10
xMatch = 1
xMismatch = -0.5
gapScore = -2

identity_cutoff = 80
minScore = 3

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


class EblScoring(Scoring):
    def __init__(self, v: Vocabulary):
        self.v = v
        self.line_break = v.encode("#")
        self.x = v.encode("X")

    def __call__(self, firstElement, secondElement):
        firstDecoded = self.v.decode(firstElement)
        secondDecoded = self.v.decode(secondElement)
        if firstElement == self.line_break or secondElement == self.line_break:
            return breakMatch if firstElement == secondElement else breakMismatch
        elif firstElement == self.x or secondElement == self.x:
            return xMatch if firstElement == secondElement else xMismatch
        elif frozenset([firstDecoded, secondDecoded]) in curated_substitutions:
            return commonMismatch
        elif "/" in firstDecoded or "/" in secondDecoded:
            result = []
            for a in firstDecoded.split("/"):
                for b in secondDecoded.split("/"):
                    result.append(self(self.v.encode(a), self.v.encode(b)))
            return max(result)
        elif firstElement == secondElement:
            return match
        else:
            return mismatch
