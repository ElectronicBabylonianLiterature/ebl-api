from collections import Counter
import itertools
import time
import re

from alignment.vocabulary import Vocabulary

from ebl.app import create_context
from ebl.ebl_scoring import print_config
from ebl.transliteration.domain.genre import Genre
from ebl.corpus.domain.chapter import ChapterId, TextId, Stage
from ebl.align import align, make_sequence, print_counter, NamedSequence

verbose = False
all = True
i2 = ChapterId(TextId(Genre.LITERATURE, 1, 2), Stage.STANDARD_BABYLONIAN, "I")
iii3 = ChapterId(TextId(Genre.LITERATURE, 3, 3), Stage.STANDARD_BABYLONIAN, "-")
iii4 = ChapterId(TextId(Genre.LITERATURE, 3, 4), Stage.STANDARD_BABYLONIAN, "-")

context = create_context()
repository = context.text_repository


def align_chapter_manuscripts(chapter):
    if(not any(chapter.signs)):
        return Counter()
    elif verbose:
        print(f"{chapter.id_}   ".ljust(80, "≡"), end="\n\n", flush=True)

    t0 = time.time()
    v = Vocabulary()

    sequences = [
        NamedSequence(
            f"{chapter.id_} {chapter.manuscripts[index].siglum}",
            v.encodeSequence(make_sequence(string)),
        )
        for index, string in enumerate(chapter.signs)
        if not re.fullmatch(r"[X\\n\s]*", string)
    ]

    pairs = itertools.combinations(sequences, 2)
    c = align(pairs, v, verbose)

    t = time.time()
    if verbose:
        print(f"Time: {(t-t0)/60} min", end="\n\n", flush=True)
    else:
        print("", flush=True)

    return c


print_config()
print()
print("query, target, score, preserved identity, preserved similarity")

c = Counter()

if all:
    t0 = time.time()
    for text in repository.list():
        for listing in text.chapters:
            chapter = repository.find_chapter(ChapterId(text.id, listing.stage, listing.name))
            c = c + align_chapter_manuscripts(chapter)

    if verbose:
        print("\n\nSubstitutions", end="\n\n")
        print_counter(c)

    print("\n\n")
    print(f"Time: {(t-t0)/60} min", flush=True)
else:
    chapter = repository.find_chapter(iii4)
    align_chapter_manuscripts(chapter)
