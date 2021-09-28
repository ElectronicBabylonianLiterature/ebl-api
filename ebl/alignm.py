import itertools
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
chapter = repository.find_chapter(ChapterId(TextId(Genre.LITERATURE, 1, 2),Stage.STANDARD_BABYLONIAN, "I"))
print(chapter.id_, end="\n\n")

t0 = time.time()
v = Vocabulary()

sequences = [
    (chapter.manuscripts[index].siglum, v.encodeSequence(Sequence(string.replace("\n", " # ").split(" "))))
    for index, string in enumerate(chapter.signs)
    if not re.fullmatch(r"[X\\n\s]*", string)
]


pairs = itertools.combinations(sequences, 2)
align(pairs, v)

t = time.time()
print(f"Time: {(t-t0)/60} min\n")
