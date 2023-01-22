from alignment.sequence import Sequence
from alignment.vocabulary import Vocabulary
from alignment.sequencealigner import SimpleScoring, GlobalSequenceAligner

# Create sequences to be aligned.
a = Sequence('what a beautiful day'.split())
b = Sequence('what a disappointingly bad day'.split())

# Create a vocabulary and encode the sequences.
v = Vocabulary()
aEncoded = v.encodeSequence(a)
bEncoded = v.encodeSequence(b)

# Create a scoring and align the sequences using global aligner.
scoring = SimpleScoring(2, -1)
aligner = GlobalSequenceAligner(scoring, -2)
score, encodeds = aligner.align(aEncoded, bEncoded, backtrace=True)

# Iterate over optimal alignments and print them.
for encoded in encodeds:
    alignment = v.decodeSequenceAlignment(encoded)
    print(alignment)
    print('Alignment score:', alignment.score)
    print('Percent identity:', alignment.percentIdentity())
    print()