import argparse
import csv
from functools import partial
import re
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import sys
import time
from typing import Iterable, List, Tuple

from alignment.vocabulary import Vocabulary
from tqdm import tqdm

from ebl.alignment.application.align import align
from ebl.alignment.domain.result import AlignmentResult
from ebl.alignment.domain.sequence import NamedSequence
from ebl.app import create_context
from ebl.context import Context
from ebl.corpus.domain.chapter import ChapterId, Chapter
from ebl.corpus.domain.text import Text
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.transliteration.domain.museum_number import MuseumNumber


def has_clear_signs(signs: str) -> bool:
    return not re.fullmatch(r"[X\\n\s]*", signs)


def align_fragment_and_chapter(
    fragment: Fragment, chapter: Chapter
) -> List[AlignmentResult]:
    vocabulary = Vocabulary()
    fragment_sequence = NamedSequence.of_fragment(fragment, vocabulary)

    pairs = [
        (
            fragment_sequence,
            NamedSequence.of_signs(
                chapter.manuscripts[index].siglum, signs, vocabulary
            ),
        )
        for index, signs in enumerate(chapter.signs)
        if signs is not None and has_clear_signs(signs)
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
    if not result.alignments:
        return {**common, "score": result.score}
    alignment = result.alignments[0]
    return {
        **common,
        "score": alignment.score,
        "preserved identity": round(alignment.percentPreservedIdentity(), 2),
        "preserved similarity": round(alignment.percentPreservedSimilarity(), 2),
    }


def align_fragment(
    number: MuseumNumber,
    chapters: Iterable[Tuple[Text, Chapter]],
    max_lines: int,
    min_score: int,
) -> List[dict]:
    sys.setrecursionlimit(50000)
    context = create_context()
    fragment = context.fragment_repository.query_by_museum_number(number)

    return (
        [
            to_dict(fragment, text, chapter, result)
            for (text, chapter) in chapters
            for result in align_fragment_and_chapter(fragment, chapter)
            if result.score >= min_score
        ]
        if fragment.text.number_of_lines <= max_lines
        else []
    )


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
        "-l", "--limit", type=int, default=25000, help="Number of fragments to align."
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
        default=10,
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
        "-w", "--workers", default=None, help="Number of parallel workers."
    )
    parser.add_argument(
        "-t",
        "--threads",
        action="store_true",
        default=True,
        help="Use threads instead of processes.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    start = args.skip
    end = args.skip + args.limit

    context = create_context()
    fragments = context.fragment_repository

    t0 = time.time()

    fragment_numbers = fragments.query_transliterated_numbers()[start:end]
    chapters = load_chapters(context)

    Executor = ThreadPoolExecutor if args.threads else ProcessPoolExecutor

    with (
        Executor(max_workers=args.workers) as executor,
        open(args.output, "w", encoding="utf-8") as file,
    ):
        results = tqdm(
            executor.map(
                partial(
                    align_fragment,
                    chapters=chapters,
                    max_lines=args.max_lines,
                    min_score=args.min_score,
                ),
                fragment_numbers,
            ),
            total=len(fragment_numbers),
        )

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

        for fragment_results in results:
            for result in fragment_results:
                writer.writerow(result)

    t = time.time()
    print(f"\nTime: {round((t - t0) / 60, 2)} min")
