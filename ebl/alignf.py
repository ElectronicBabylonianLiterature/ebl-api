import sys
import time
import re

from alignment.sequence import Sequence
from alignment.vocabulary import Vocabulary
from alignment.sequencealigner import LocalSequenceAligner

from ebl.app import create_context
from ebl.transliteration.domain.genre import Genre
from ebl.corpus.domain.chapter import ChapterId, TextId, Stage
from ebl.ebl_scoring import EblScoring

sys.setrecursionlimit(10000)

context = create_context()
repository = context.text_repository
chapter = repository.find_chapter(
    ChapterId(TextId(Genre.LITERATURE, 1, 2), Stage.STANDARD_BABYLONIAN, "I")
)
print(chapter.id_, end="\n\n")

fragments = []
for manuscript in chapter.manuscripts:
    if manuscript.museum_number is not None:
        try:
            fragment = context.fragment_repository.query_by_museum_number(
                manuscript.museum_number
            )

            if not re.fullmatch(r"[X\\n\s]*", fragment.signs):
                fragments.append((fragment.number, fragment.signs))
        except Exception:
            pass

t0 = time.time()
v = Vocabulary()

fsequences = [
    (number, v.encodeSequence(Sequence(string.replace("\n", " # ").split(" "))))
    for number, string in fragments
]

sequences = [
    (
        chapter.manuscripts[index].siglum,
        v.encodeSequence(Sequence(string.replace("\n", " # ").split(" "))),
    )
    for index, string in enumerate(chapter.signs)
    if not re.fullmatch(r"[X\\n\s]*", string)
]

no_alignment = []
results = []
x = 1
for a in fsequences:
    for b in sequences:
        aEncoded = a[1]
        bEncoded = b[1]

        # Create a scoring and align the sequences using global aligner.
        scoring = EblScoring(2, -1, v)
        aligner = LocalSequenceAligner(scoring, -2)
        score, encodeds = aligner.align(aEncoded, bEncoded, backtrace=True)

        if score > 0 and len(encodeds) > 0:
            results.append((x, a[0], b[0], score, encodeds))
        else:
            no_alignment.append((a[0], b[0]))
        x += 1

t = time.time()
print(f"Time: {(t-t0)/60} min\n")

for result in sorted(
    results, key=lambda result: (result[4][0].percentIdentity(),result[4][0].score), reverse=True
):
    encodeds = result[4]
    alignments = [v.decodeSequenceAlignment(encoded) for encoded in encodeds]
    alignments = [
        alignment
        for alignment in alignments
        if not any([re.fullmatch(r"[X\s#\-]+", row) for row in str(alignment).split("\n")])
    ]
    if alignments:
        print(
            f"\n{result[0]} == {result[1]} vs {result[2]} ============================================="
        )

        for alignment in alignments:
            print(alignment)
            print("Alignment score:", alignment.score)
            print("Percent identity:", alignment.percentIdentity())
            print("Percent similarity:", alignment.percentSimilarity())
            print()
