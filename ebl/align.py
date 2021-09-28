import itertools
import sys
import time

from alignment.sequence import Sequence
from alignment.vocabulary import Vocabulary
from alignment.sequencealigner import SimpleScoring, GlobalSequenceAligner

from ebl.app import create_context
from ebl.transliteration.domain.genre import Genre
from ebl.corpus.domain.chapter import ChapterId, TextId, Stage

sys.setrecursionlimit(10000)

context = create_context()
repository = context.text_repository
chapter = repository.find_chapter(ChapterId(TextId(Genre.LITERATURE, 1, 2),Stage.STANDARD_BABYLONIAN, "I"))

t0 = time.time()
v = Vocabulary()

sequences = [
    (chapter.manuscripts[index].siglum, v.encodeSequence(Sequence(string.replace("\n", " # ").split(" "))))
    for index, string in enumerate(chapter.signs)
]

print(chapter.id_, end="\n\n")

no_alignment = []
x = 1
for a, b in itertools.combinations(sequences, 2):
    aEncoded = a[1]
    bEncoded = b[1]

    # Create a scoring and align the sequences using global aligner.
    scoring = SimpleScoring(2, -1)
    aligner = GlobalSequenceAligner(scoring, -2)
    score, encodeds = aligner.align(aEncoded, bEncoded, backtrace=True)

    if score > 0:
        print(f"\n{x} == {a[0]} vs {b[0]} =============================================")
        # Iterate over optimal alignments and print them.
        for encoded in encodeds:
            alignment = v.decodeSequenceAlignment(encoded)
            print(alignment)
            print("Alignment score:", alignment.score)
            print("Percent identity:", alignment.percentIdentity())
            print()
    else:
        no_alignment.append((a[0], b[0]))
    x += 1

t = time.time()

print(f"\nNo aligment found ({len(no_alignment)}):")
for a,b in no_alignment:
    print(a, ", ", b)

print(f"\n\nTime: {(t-t0)/60} min")
