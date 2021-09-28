from alignment.sequencealigner import Scoring
from alignment.vocabulary import Vocabulary

match = 2
mismatch = -1
breakMatch = 2
breakMismatch = -10
xMatch = 1
xMismatch = -0.5


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
