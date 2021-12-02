import argparse
import re
import math
import sys
import time
from typing import Iterable, List

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
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.museum_number import MuseumNumber


def has_clear_signs(signs: str) -> bool:
    return not re.fullmatch(r"[X\\n\s]*", signs)


def make_title(chapter: Chapter, index: int, fragment: Fragment) -> str:
    has_same_number = fragment.number == chapter.manuscripts[index].museum_number
    return (
        f"{chapter.id_}, "
        f"{chapter.manuscripts[index].siglum}"
        f"{'*' if has_same_number else ''}"
    )


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


def align_fragment(
    fragment: Fragment, chapters: Iterable[Chapter]
) -> List[AlignmentResult]:
    return [
        result
        for chapter in chapters
        for result in align_fragment_and_chapter(fragment, chapter)
    ]


def align_chunck(
    id_: int,
    numbers: Iterable[MuseumNumber],
    chapters: Iterable[Chapter],
    max_lines: int,
    min_score: int,
) -> List[str]:
    sys.setrecursionlimit(50000)
    context = create_context()
    results = []
    for number in tqdm(numbers, desc=f"Chunk #{id_}", position=id_):
        fragment = context.fragment_repository.query_by_museum_number(number)
        results.extend(
            result.to_csv()
            for result in align_fragment(fragment, chapters)
            if fragment.text.number_of_lines <= max_lines
            if result.score >= min_score
        )

    return results


def load_chapters(context: Context) -> List[Chapter]:
    texts = context.text_repository
    return [
        chapter
        for chapter in (
            texts.find_chapter(ChapterId(text.id, listing.stage, listing.name))
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
        delayed(align_chunck)(index, subset, chapters, args.max_lines, args.min_score)
        for index, subset in enumerate(chunks)
    )

    t = time.time()

    with open(args.output, "w", encoding="utf-8") as file:
        file.write(
            "fragment, chapter, manuscript, score, preserved identity, preserved similarity\n"
        )
        file.writelines(f"{result}\n" for chunk in results for result in chunk)
        file.write(f"# Time: {(t-t0)/60} min")

    print("\nDone.")
