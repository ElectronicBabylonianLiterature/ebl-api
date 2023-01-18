import time
import re
from collections import Counter

from alignment.vocabulary import Vocabulary

from ebl.app import create_context
from ebl.transliteration.domain.genre import Genre
from ebl.corpus.domain.chapter import ChapterId, TextId, Stage
from ebl.align import align, make_sequence, print_counter, NamedSequence

all = False
i2 = ChapterId(TextId(Genre.LITERATURE, 1, 2), Stage.STANDARD_BABYLONIAN, "I")
iii3 = ChapterId(TextId(Genre.LITERATURE, 3, 3), Stage.STANDARD_BABYLONIAN, "-")
iii4 = ChapterId(TextId(Genre.LITERATURE, 3, 4), Stage.STANDARD_BABYLONIAN, "-")

context = create_context()
repository = context.text_repository


def align_chapter_manuscripts(chapter):
    if not any(chapter.signs):
        return Counter()
    else:
        print(f"{chapter.id_}   ".ljust(80, "≡"), end="\n\n", flush=True)

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
        NamedSequence(number, v.encodeSequence(make_sequence(string)))
        for number, string in fragments
    ]

    sequences = [
        NamedSequence(
            chapter.manuscripts[index].siglum, v.encodeSequence(make_sequence(string))
        )
        for index, string in enumerate(chapter.signs)
        if not re.fullmatch(r"[X\\n\s]*", string)
    ]

    pairs = []
    for a in fsequences:
        for b in sequences:
            pairs.append((a, b))

    c = align(pairs, v, not all)

    t = time.time()
    print(f"Time: {(t-t0)/60} min", end="\n\n", flush=True)

    return c


c = Counter()
if all:
    for text in repository.list():
        for listing in text.chapters:
            chapter = repository.find_chapter(
                ChapterId(text.id, listing.stage, listing.name)
            )
            c = c + align_chapter_manuscripts(chapter)

    print("\n\nSubstitutions", end="\n\n")
    print_counter(c)
else:
    chapter = repository.find_chapter(iii4)
    align_chapter_manuscripts(chapter)
