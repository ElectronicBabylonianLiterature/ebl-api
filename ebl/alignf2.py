import time
import re
from typing import Counter

from alignment.vocabulary import Vocabulary

from ebl.app import create_context
from ebl.ebl_scoring import print_config
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.genre import Genre
from ebl.corpus.domain.chapter import ChapterId, TextId, Stage
from ebl.align import align, make_sequence, print_counter, NamedSequence

verbose = False
all = True
i2 = ChapterId(TextId(Genre.LITERATURE, 1, 2), Stage.STANDARD_BABYLONIAN, "I")
iii3 = ChapterId(TextId(Genre.LITERATURE, 3, 3), Stage.STANDARD_BABYLONIAN, "-")
iii4 = ChapterId(TextId(Genre.LITERATURE, 3, 4), Stage.STANDARD_BABYLONIAN, "-")
k17700 = MuseumNumber.of("K.17700")  #
k19352 = MuseumNumber.of("K.19352")  #

test_set = [
    MuseumNumber.of("BM.36681"),  # School
    MuseumNumber.of("BM.36688"),  # School
    MuseumNumber.of("BM.99811"),  # School, matches two texts
    MuseumNumber.of("BM.101558"),  # School, matches two texts
    MuseumNumber.of("K.20949"),  # School, matches two texts
    MuseumNumber.of("K.17591"),  # Fragment
    MuseumNumber.of("K.18617"),  # Fragment
    MuseumNumber.of("K.19604"),  # Fragment
    MuseumNumber.of("K.20637"),  # Fragment
    MuseumNumber.of("K.21209"),  # Fragment
    MuseumNumber.of("Rm.468"),  # Fragment
]


context = create_context()
repository = context.text_repository


def align_fragment_and_chapter(fragment, chapter):
    if not any(chapter.signs):
        return Counter()

    t0 = time.time()
    v = Vocabulary()

    fsequence = NamedSequence(
        fragment.number, v.encodeSequence(make_sequence(fragment.signs))
    )

    sequences = [
        NamedSequence(
            f"{chapter.id_}, {chapter.manuscripts[index].siglum}{'*' if fragment.number == chapter.manuscripts[index].museum_number else ''}",
            v.encodeSequence(make_sequence(string)),
        )
        for index, string in enumerate(chapter.signs)
        if not re.fullmatch(r"[X\\n\s]*", string)
    ]

    pairs = [(fsequence, b) for b in sequences]
    c = align(pairs, v, verbose, lambda result: result.score)

    t = time.time()
    if verbose:
        print(f"Time: {(t-t0)/60} min", end="\n\n", flush=True)

    return c


chapters = [
    repository.find_chapter(ChapterId(text.id, listing.stage, listing.name))
    for text in repository.list()
    for listing in text.chapters
]


def align_fragment(number):
    t0 = time.time()
    c = Counter()

    fragment = context.fragment_repository.query_by_museum_number(number)

    for chapter in chapters:
        c = c + align_fragment_and_chapter(fragment, chapter)

    t = time.time()
    if verbose:
        print("\n\n")
        print(f"Time: {(t-t0)/60} min", flush=True)
        print("Substitutions", end="\n\n")
        print_counter(c)
    else:
        print()


print_config()


print()
print("fragment, chapter, manuscript, score, preserved identity, preserved similarity")

t0 = time.time()

for number in test_set:
    align_fragment(number)

t = time.time()

print("\n\n")
print(f"Time: {(t-t0)/60} min", flush=True)
