import argparse
import re
import sys
import time
from typing import Iterable

from alignment.vocabulary import Vocabulary  # pyre-ignore[21]

from ebl.alignment.application.align import align
from ebl.alignment.domain.sequence import NamedSequence
from ebl.app import create_context
from ebl.corpus.domain.chapter import ChapterId, Chapter
from ebl.fragmentarium.domain.fragment import Fragment


def has_clear_signs(signs: str) -> bool:
    return not re.fullmatch(r"[X\\n\s]*", signs)


def make_title(chapter: Chapter, index: int, fragment: Fragment) -> str:
    has_same_number = fragment.number == chapter.manuscripts[index].museum_number
    return (
        f"{chapter.id_}, "
        f"{chapter.manuscripts[index].siglum}"
        f"{'*' if has_same_number else ''}"
    )


def align_fragment_and_chapter(fragment: Fragment, chapter: Chapter) -> None:
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
    print(align(pairs, vocabulary, lambda result: result.score), flush=True)


def align_fragment(fragment: Fragment, chapters: Iterable[Chapter]) -> None:
    fragment = context.fragment_repository.query_by_museum_number(number)

    for chapter in chapters:
        align_fragment_and_chapter(fragment, chapter)

    print("", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s", "--skip", type=int, default=0, help="Number of fragments to skip."
    )
    parser.add_argument(
        "-l", "--limit", type=int, default=10, help="Number of fragments to align."
    )
    args = parser.parse_args()
    start = args.skip
    end = args.skip + args.limit

    sys.setrecursionlimit(50000)

    context = create_context()
    texts = context.text_repository
    fragments = context.fragment_repository

    print(
        "fragment, chapter, manuscript, score, preserved identity, preserved similarity"
    )

    t0 = time.time()

    fragment_numbers = fragments.query_transliterated_numbers()
    chapters = [
        texts.find_chapter(ChapterId(text.id, listing.stage, listing.name))
        for text in texts.list()
        for listing in text.chapters
    ]
    chapters_with_signs = [chapter for chapter in chapters if any(chapter.signs)]

    for number in fragment_numbers[start:end]:
        fragment = fragments.query_by_museum_number(number)
        align_fragment(fragment, chapters_with_signs)

    t = time.time()

    print(f"# Time: {(t-t0)/60} min", flush=True)
