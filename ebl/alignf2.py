import time
import re
from typing import Counter

from alignment.vocabulary import Vocabulary

from ebl.app import create_context
from ebl.ebl_scoring import print_config
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.genre import Genre
from ebl.corpus.domain.chapter import ChapterId, TextId, Stage
from ebl.align import align, make_sequence, print_counter

all = True
i2 = ChapterId(TextId(Genre.LITERATURE, 1, 2), Stage.STANDARD_BABYLONIAN, "I")
iii3 = ChapterId(TextId(Genre.LITERATURE, 3, 3), Stage.STANDARD_BABYLONIAN, "-")
iii4 = ChapterId(TextId(Genre.LITERATURE, 3, 4), Stage.STANDARD_BABYLONIAN, "-")
k17700 = MuseumNumber.of("K.17700")
k19352 = MuseumNumber.of("K.19352")

context = create_context()
repository = context.text_repository


def align_fragment(fragment, chapter):
    if not any(chapter.signs):
        return Counter()
    else:
        print(f"{chapter.id_}   ".ljust(80, "≡"), end="\n\n", flush=True)

    t0 = time.time()
    v = Vocabulary()

    fsequence = (fragment.number, v.encodeSequence(make_sequence(fragment.signs)))

    sequences = [
        (chapter.manuscripts[index].siglum, v.encodeSequence(make_sequence(string)))
        for index, string in enumerate(chapter.signs)
        if not re.fullmatch(r"[X\\n\s]*", string)
    ]

    pairs = [(fsequence, b) for b in sequences]
    c = align(pairs, v, True, lambda result: result[3])

    t = time.time()
    print(f"Time: {(t-t0)/60} min", end="\n\n", flush=True)

    return c


print_config()

c = Counter()
fragment = context.fragment_repository.query_by_museum_number(k17700)
if all:
    for text in repository.list():
        for listing in text.chapters:
            chapter = repository.find_chapter(
                ChapterId(text.id, listing.stage, listing.name)
            )
            c = c + align_fragment(fragment, chapter)

    print("\n\nSubstitutions", end="\n\n")
    print_counter(c)
else:
    chapter = repository.find_chapter(iii4)
    align_fragment(fragment, chapter)
