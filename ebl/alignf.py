import sys
import time
import re

from alignment.sequence import Sequence
from alignment.vocabulary import Vocabulary

from ebl.app import create_context
from ebl.transliteration.domain.genre import Genre
from ebl.corpus.domain.chapter import ChapterId, TextId, Stage
from ebl.align import align

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
    (number, v.encodeSequence(Sequence(re.sub(r" +", " ", string.replace("\n", " # ").replace("X", " ")).strip().split(" "))))
    for number, string in fragments
]

sequences = [
    (
        chapter.manuscripts[index].siglum,
        v.encodeSequence(Sequence(re.sub(r" +", " ", string.replace("\n", " # ").replace("X", " ")).strip().split(" "))),
    )
    for index, string in enumerate(chapter.signs)
    if not re.fullmatch(r"[X\\n\s]*", string)
]

pairs = []
for a in fsequences:
    for b in sequences:
        pairs.append((a,b))

align(pairs, v)

t = time.time()
print(f"Time: {(t-t0)/60} min\n")
