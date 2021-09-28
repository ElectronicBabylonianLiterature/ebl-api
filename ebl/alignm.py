import itertools
import time
import re

from alignment.sequence import Sequence
from alignment.vocabulary import Vocabulary

from ebl.app import create_context
from ebl.transliteration.domain.genre import Genre
from ebl.corpus.domain.chapter import ChapterId, TextId, Stage
from ebl.align import align, make_sequence

i2 = ChapterId(TextId(Genre.LITERATURE, 1, 2), Stage.STANDARD_BABYLONIAN, "I")
iii3 = ChapterId(TextId(Genre.LITERATURE, 3, 3), Stage.STANDARD_BABYLONIAN, "I")

context = create_context()
repository = context.text_repository
chapter = repository.find_chapter(iii3)
print(chapter.id_, end="\n\n")

t0 = time.time()
v = Vocabulary()

sequences = [
    (
        chapter.manuscripts[index].siglum,
        v.encodeSequence(make_sequence(string)),
    )
    for index, string in enumerate(chapter.signs)
    if not re.fullmatch(r"[X\\n\s]*", string)
]


pairs = itertools.combinations(sequences, 2)
align(pairs, v)

t = time.time()
print(f"Time: {(t-t0)/60} min\n")
