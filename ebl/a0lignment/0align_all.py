import csv
import re
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import partial

import attr
import pyalign
from alignment.vocabulary import Vocabulary
from tqdm import tqdm

from ebl.a0lignment.sequence import NamedSequence
from ebl.app import create_context
from ebl.context import Context
from ebl.corpus.domain.chapter import ChapterId

vocabulary = Vocabulary()

def has_clear_signs(signs: str) -> bool:
    return not re.fullmatch(r"[X\\n\s]*", signs)

@attr.s(auto_attribs=True, frozen=True)
class AlignmentResult:
    a: NamedSequence
    b: NamedSequence
    alignment: any
    score: float


def align_pairs(pairs):
    alignments = []
    for pair in pairs:
        a, b = pair
        alignment = pyalign.global_alignment(a.sequence, b.sequence, gap_Cost=0, eq=2, ne=-0.1)
        alignments.append(AlignmentResult(a, b, alignment=alignment, score=alignment.score))
    return sorted(alignments, key=lambda x: x.score, reverse=True)


def _align_fragment(fragment, chapter):
    fragment_sequence = NamedSequence.of_fragment(fragment["_id"], fragment["signs"], vocabulary)

    pairs = [
        (
            fragment_sequence,
            NamedSequence.of_signs(
                chapter.manuscripts[index].siglum, signs, vocabulary
            ),
        )
        for index, signs in enumerate(chapter.signs)
        if has_clear_signs(signs)
    ]
    return align_pairs(pairs)

def to_dict(
    result
) -> dict:
    return {
        "fragment": result.a.name,
        "manuscript": result.b.name,
        "score": result.score
    }

def align_fragment(number, chapters):
    context = create_context()
    fragment = context.fragment_repository.query_by_museum_number_alignment(number)
    results = []
    for text, chapter in chapters:
        for result in _align_fragment(fragment, chapter):
            results.append(to_dict(result))

    return results

def load_chapters(context: Context):
    texts = context.text_repository
    chapters = []
    for text in texts.list_alignment():
        for listing in text.chapters:
            chapter = texts.find_chapter_for_alignment(ChapterId(text.id, listing.stage, listing.name))
            if any(chapter.signs):
                chapters.append((text, chapter))
    return chapters




if __name__ == "__main__":
    t0 = time.time()
    context = create_context()
    repository = context.text_repository
    fragments = context.fragment_repository

    fragment_numbers = fragments.query_transliterated_numbers()
    chapters = load_chapters(context)

    threads = True
    workers = None
    output = "./output.csv"


    #asd = align_fragment(fragment_numbers[0], chapters)



    Executor = ThreadPoolExecutor if threads else ProcessPoolExecutor

    with Executor(max_workers=workers) as executor, open(
        output, "w", encoding="utf-8"
    ) as file:
        results = tqdm(
            executor.map(
                partial(
                    align_fragment,
                    chapters=chapters,
                ),
                fragment_numbers,
            ),
            total=len(fragment_numbers),
        )

        fieldnames = [
            "fragment",
            "manuscript",
            "score",
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for fragment_results in results:
            for result in fragment_results:
                writer.writerow(result)


    t = time.time()
    print(f"\nTime: {round((t-t0)/60, 2)} min")
