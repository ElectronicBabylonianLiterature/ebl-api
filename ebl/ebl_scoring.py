from alignment.sequencealigner import Scoring
from alignment.vocabulary import Vocabulary


class EblScoring(Scoring):
    def __init__(self, matchScore, mismatchScore, v: Vocabulary):
        self.v = v
        self.matchScore = matchScore
        self.mismatchScore = mismatchScore
        self.line_break = v.encode("#")
        self.x = v.encode("X")

    def __call__(self, firstElement, secondElement):
        firstDecoded = self.v.decode(firstElement)
        secondDecoded = self.v.decode(secondElement)
        if firstElement == self.line_break or secondElement == self.line_break:
            return self.matchScore if firstElement == secondElement else -10
        elif firstElement == self.x or secondElement == self.x:
            return 1 if firstElement == secondElement else -0.5
        elif "/" in firstDecoded or "/" in secondDecoded:
            result = []
            for a in firstDecoded.split("/"):
                for b in secondDecoded.split("/"):
                    result.append(self(self.v.encode(a), self.v.encode(b)))
            print("XXX", firstDecoded, secondDecoded, result)
            return max(result)
        elif firstElement == secondElement:
            return self.matchScore
        else:
            return self.mismatchScore
