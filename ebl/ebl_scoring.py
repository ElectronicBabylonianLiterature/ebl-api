from alignment.sequencealigner import Scoring
from alignment.vocabulary import Vocabulary


class EblScoring(Scoring):
    def __init__(self, matchScore, mismatchScore, v: Vocabulary):
        self.matchScore = matchScore
        self.mismatchScore = mismatchScore
        self.line_break = v.encode("#")
        self.x = v.encode("X")

    def __call__(self, firstElement, secondElement):
        if firstElement == self.line_break or secondElement == self.line_break:
            return self.matchScore if firstElement == secondElement else -10
        elif firstElement == self.x or secondElement == self.x:
            return 1 if firstElement == secondElement else -0.5
        elif firstElement == secondElement:
            return self.matchScore
        else:
            return self.mismatchScore
