import argparse
from functools import reduce
from multiprocessing import Pool
from typing import List

import attr
from tqdm import tqdm

from ebl.app import create_context
from ebl.corpus.application.corpus import Corpus
from ebl.corpus.domain.chapter import ChapterId
from ebl.corpus.domain.text import Text, TextId
from ebl.users.domain.user import ApiUser
from ebl.corpus.domain.lines_update import LinesUpdate


def update_text(corpus: Corpus, text: Text) -> None:
    user = ApiUser("update_texts.py")
    for chapter_listing in text.chapters:
        chapter_id = ChapterId(text.id, chapter_listing.stage, chapter_listing.name)
        chapter = corpus.find_chapter(chapter_id)
        corpus.update_lines(
            chapter_id,
            LinesUpdate([], set(), dict(enumerate(chapter.lines))),
            user,
        )


@attr.s(auto_attribs=True)
class State:
    invalid: int = 0
    updated: int = 0
    errors: List[str] = attr.ib(factory=list)

    def add_updated(self) -> None:
        self.updated += 1

    def add_error(self, error: Exception, text: Text) -> None:
        self.invalid += 1
        self.errors.append(f"{text.category} {text.index}\t{error}")

    def to_tsv(self) -> str:
        return "\n".join(
            [*self.errors, f"# Updated: {self.updated}", f"# Invalid: {self.invalid}"]
        )

    def merge(self, other: "State") -> "State":
        return State(
            self.invalid + other.invalid,
            self.updated + other.updated,
            self.errors + other.errors,
        )


def update(number) -> State:
    context = create_context()
    corpus = Corpus(
        context.text_repository,
        context.get_bibliography(),
        context.changelog,
        context.sign_repository,
        context.parallel_line_injector,
    )
    state = State()
    text = corpus.find(number)

    try:
        update_text(corpus, text)
        state.add_updated()
    except Exception as error:
        state.add_error(error, text)

    return state


def get_text_ids() -> List[TextId]:
    context = create_context()
    corpus = Corpus(
        context.text_repository,
        context.get_bibliography(),
        context.changelog,
        context.sign_repository,
        context.parallel_line_injector,
    )
    return [text.id for text in corpus.list()]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        help="number of parallel workers to perform migration",
        default=4,
    )
    args = parser.parse_args()

    numbers = get_text_ids()

    with Pool(processes=args.workers) as pool:
        states = tqdm(pool.imap_unordered(update, numbers), total=len(numbers))
        final_state = reduce(
            lambda accumulator, state: accumulator.merge(state), states, State()
        )

    with open("invalid_texts.tsv", "w", encoding="utf-8") as file:
        file.write(final_state.to_tsv())

    print("Update texts completed!")
