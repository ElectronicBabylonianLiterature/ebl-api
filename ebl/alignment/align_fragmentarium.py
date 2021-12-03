import argparse
import csv
import re
import math
import sys
import time
from typing import Iterable, List, Tuple

from alignment.vocabulary import Vocabulary  # pyre-ignore[21]
from joblib import Parallel, delayed
import pydash
from tqdm import tqdm

from ebl.alignment.application.align import align
from ebl.alignment.domain.result import AlignmentResult
from ebl.alignment.domain.sequence import NamedSequence
from ebl.app import create_context
from ebl.context import Context
from ebl.corpus.domain.chapter import ChapterId, Chapter
from ebl.corpus.domain.text import Text
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.museum_number import MuseumNumber


def has_clear_signs(signs: str) -> bool:
    return not re.fullmatch(r"[X\\n\s]*", signs)


def make_title(chapter: Chapter, index: int, fragment: Fragment) -> str:
    has_same_number = fragment.number == chapter.manuscripts[index].museum_number
    siglum = chapter.manuscripts[index].siglum
    return f"{siglum}{'*' if has_same_number else ''}"


def align_fragment_and_chapter(
    fragment: Fragment, chapter: Chapter
) -> List[AlignmentResult]:
    vocabulary = Vocabulary()
    fragment_sequence = NamedSequence.of_signs(
        fragment.number, fragment.signs, vocabulary
    )

    pairs = [
        (
            fragment_sequence,
            NamedSequence.of_signs(
                make_title(chapter, index, fragment), signs, vocabulary
            ),
        )
        for index, signs in enumerate(chapter.signs)
        if has_clear_signs(signs)
    ]

    return align(pairs, vocabulary)


def to_dict(
    fragment: Fragment, text: Text, chapter: Chapter, result: AlignmentResult
) -> dict:
    common = {
        "fragment": result.a.name,
        "manuscript": result.b.name,
        "text id": text.id,
        "text name": text.name,
        "chapter": f"{chapter.stage.abbreviation} {chapter.name}",
        "notes": fragment.notes,
    }
    if result.alignments:
        alignment = result.alignments[0]
        return {
            **common,
            "score": alignment.score,
            "preserved identity": round(alignment.percentPreservedIdentity(), 2),
            "preserved similarity": round(alignment.percentPreservedSimilarity(), 2),
        }
    else:
        return {**common, "score": result.score}


def align_fragment(
    fragment: Fragment, chapters: Iterable[Tuple[Text, Chapter]], min_score: int
) -> List[dict]:
    return [
        to_dict(fragment, text, chapter, result)
        for (text, chapter) in chapters
        for result in align_fragment_and_chapter(fragment, chapter)
        if result.score >= min_score
    ]


def align_chunk(
    id_: int,
    numbers: Iterable[MuseumNumber],
    chapters: Iterable[Tuple[Text, Chapter]],
    max_lines: int,
    min_score: int,
) -> List[dict]:
    sys.setrecursionlimit(50000)
    context = create_context()
    results: List[dict] = []
    for number in tqdm(numbers, desc=f"Chunk #{id_}", position=id_):
        fragment = context.fragment_repository.query_by_museum_number(number)
        if fragment.text.number_of_lines <= max_lines:
            results.extend(align_fragment(fragment, chapters, min_score))

    return results


def load_chapters(context: Context) -> List[Tuple[Text, Chapter]]:
    texts = context.text_repository
    return [
        (text, chapter)
        for (text, chapter) in (
            (text, texts.find_chapter(ChapterId(text.id, listing.stage, listing.name)))
            for text in texts.list()
            for listing in text.chapters
        )
        if any(chapter.signs)
    ]


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s", "--skip", type=int, default=0, help="Number of fragments to skip."
    )
    parser.add_argument(
        "-l", "--limit", type=int, default=10, help="Number of fragments to align."
    )
    parser.add_argument(
        "--minScore",
        dest="min_score",
        type=int,
        default=100,
        help="Minimum score to show in the results.",
    )
    parser.add_argument(
        "--maxLines",
        dest="max_lines",
        type=int,
        default=20,
        help="Maximum size of fragment to align.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="alignment.csv",
        help="Filename for saving the results.",
    )
    parser.add_argument(
        "-w", "--workers", type=int, default=4, help="Number of parallel workers."
    )
    parser.add_argument(
        "-t",
        "--threads",
        action="store_true",
        help="Use threads instead of processes for workers.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    start = args.skip
    end = args.skip + args.limit
    prefer = "threads" if args.threads else None

    context = create_context()
    fragments = context.fragment_repository

    t0 = time.time()

    fragment_numbers = fragments.query_transliterated_numbers()
    chapters = load_chapters(context)

    chunk_size = math.ceil(args.limit / args.workers)
    chunks = pydash.chunk(fragment_numbers[start:end], chunk_size)

    results = Parallel(n_jobs=args.workers, prefer=prefer)(
        delayed(align_chunk)(index, subset, chapters, args.max_lines, args.min_score)
        for index, subset in enumerate(chunks)
    )

    t = time.time()

    with open(args.output, "w", encoding="utf-8") as file:
        fieldnames = [
            "fragment",
            "text id",
            "text name",
            "chapter",
            "manuscript",
            "score",
            "preserved identity",
            "preserved similarity",
            "notes",
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for chunk in results:
            for result in chunk:
                writer.writerow(result)

    print(f"\nTime: {round((t-t0)/60, 2)} min")
