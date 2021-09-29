from collections import Counter
import itertools
import time
import re

from alignment.vocabulary import Vocabulary

from ebl.app import create_context
from ebl.transliteration.domain.genre import Genre
from ebl.corpus.domain.chapter import ChapterId, TextId, Stage
from ebl.align import align, make_sequence, print_counter

i2 = ChapterId(TextId(Genre.LITERATURE, 1, 2), Stage.STANDARD_BABYLONIAN, "I")
iii3 = ChapterId(TextId(Genre.LITERATURE, 3, 3), Stage.STANDARD_BABYLONIAN, "-")
iii4 = ChapterId(TextId(Genre.LITERATURE, 3, 4), Stage.STANDARD_BABYLONIAN, "-")

context = create_context()
repository = context.text_repository

c = Counter()

for text in repository.list():
    for listing in text.chapters:
        chapter = repository.find_chapter(ChapterId(text.id, listing.stage, listing.name))
        if(not any(chapter.signs)):
            print("Skip", chapter.id_, end="\n\n", flush=True)
            continue
        else:
            print(chapter.id_, end="\n", flush=True)

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
        c = c + align(pairs, v)

        t = time.time()
        print(f"Time: {(t-t0)/60} min", end="\n\n", flush=True)

print("\n\nSubstitutions", end="\n\n")
print_counter(c)
