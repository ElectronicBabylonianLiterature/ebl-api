import itertools
import random
import math
import re
from enum import Enum, auto
import time
from collections import Counter
from typing import Mapping, Tuple

from alignment.vocabulary import Vocabulary

from ebl.align import NamedSequence, align_pair, make_sequence, print_counter
from ebl.app import create_context
from ebl.corpus.domain.chapter import ChapterId, Chapter, Stage, TextId
from ebl.ebl_scoring import print_config, minScore
from ebl.transliteration.domain.genre import Genre


verbose = False
context = create_context()
repository = context.text_repository
v = Vocabulary()
c = Counter()

def print_evaluation(c: Counter) -> None:
    precision = c[Result.TP] / (c[Result.TP] + c[Result.FP])
    recall = c[Result.TP] / (c[Result.TP] + c[Result.FN])
    f1 = 2 * (precision*recall / (precision+recall))
    f2 = (1+4) * (precision*recall / (4*precision+recall))
    print(f"precision: {precision}")
    print(f"recall: {recall}")
    print(f"f1: {f1}")
    print(f"f2: {f2}")
    print()

class Result(Enum):
    TP = auto()
    FP = auto()
    TN = auto()
    FN = auto()


chapter_results: Mapping[Tuple[str, str], Result] = {}

def align_sequences(a: NamedSequence, b: NamedSequence) -> None:
    chapter = b.name.split("; ")[0]
    expected = a.name.split("; ")[0] == chapter
    key = (a.name, chapter)
    if (a.name, chapter) not in chapter_results:
        chapter_results[key] = Result.FN if expected else Result.TN

    t0 = time.time()
    result = align_pair(a, b, v)
    t = time.time() - t0
    
    if result.score > minScore:
        result_type = Result.TP if expected else Result.FP
        chapter_results[key] = result_type
        c.update([result_type])
        print(
            f"{result.title}, {result.score}, TRUE, {str(expected).upper()}, {t}"
        )
    else:
        c.update([Result.FN if expected else Result.TN])
        print(f"{result.title}, {result.score}, FALSE, {str(expected).upper()}, {t}")


def mask(chapter: Chapter, index: int, string: str) -> NamedSequence:
    mean_size = 16
    manuscript = chapter.manuscripts[index]
    to_remove = 0  # len(manuscript.text_lines)
    all_lines = string.split("\n")
    lines = all_lines[:-to_remove] if to_remove > 0 else all_lines
    size = min(len(lines), mean_size)
    start = math.floor(random.random() * (len(lines) - size))
    masked = "\n".join(lines[start : start + size])
    return NamedSequence(
        f"{chapter.id_}; {chapter.manuscripts[index].siglum}; {start}; {size}; {len(lines)}",
        v.encodeSequence(make_sequence(masked)),
    )


print_config()
print(flush=True)


if all:
    t0 = time.time()
    chapters = [
        repository.find_chapter(ChapterId(text.id, listing.stage, listing.name))
        for text in repository.list()
        for listing in text.chapters
    ]
    target_sequences = [
        NamedSequence(
            f"{chapter.id_}; {chapter.manuscripts[index].siglum}",
            v.encodeSequence(make_sequence(string)),
        )
        for chapter in chapters
        if any(chapter.signs) and chapter.id_.text_id.category != 99
        for index, string in enumerate(chapter.signs)
        if not re.fullmatch(r"[X\\n\s]*", string)
    ]
    query_sequences = [
        NamedSequence(
            f"{chapter.id_}; {chapter.manuscripts[index].siglum}",
            v.encodeSequence(make_sequence(string)),
        )
        for chapter in chapters
        if any(chapter.signs) and chapter.id_.text_id == TextId(Genre.LITERATURE, 1, 2)
        for index, string in enumerate(chapter.signs)
        if not re.fullmatch(r"[X\\n\s]*", string) and len(string.split("\n")) <= 20
    ][:2]
    #query_sequences = random.sample(
    #    [
    #        mask(chapter, index, string)
    #        for chapter in chapters
    #        if any(chapter.signs) and chapter.id_.text_id.category != 99
    #        for index, string in enumerate(chapter.signs)
    #        if not re.fullmatch(r"[X\\n\s]*", string)
    #    ],
    #    2,
    #)
    # pairs = itertools.combinations(
    #    sequences, 2
    # )  # .combinations_with_replacement(sequences, 2)
    query_set = set(
        "; ".join(sequence.name.split("; ")[:2]) for sequence in query_sequences
    )
    pairs = list(
        itertools.product(
            query_sequences,
            [item for item in target_sequences if item.name not in query_set],
        )
    )
    print("\n".join(query_set), end="\n\n")

    print(f"{len(target_sequences)} total sequences")
    print(f"{len(query_sequences)} query sequences")
    print(f"{len(pairs)} combinations", end="\n\n")

    print(
        "query, target, score, match, expected, time (s)",
        flush=True,
    )
    for a, b in pairs:
        align_sequences(a, b)

    t = time.time()

    print("\n\nManuscript results")
    print(c)
    print_evaluation(c)

    chapter_counter = Counter(chapter_results.values())
    print("\n\nChapter results")
    for key in chapter_results:
        title = ", ".join(key)
        print(f"{title}, {chapter_results[key].name}")
    print(chapter_counter)
    print_evaluation(chapter_counter)

    print(f"Time: {(t-t0)/60} min", flush=True)
