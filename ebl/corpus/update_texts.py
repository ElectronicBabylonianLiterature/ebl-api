import math
from functools import reduce
from typing import Iterable, List

import attr
import pydash
from joblib import Parallel, delayed
from tqdm import tqdm

from ebl.app import create_context

from ebl.corpus.application.corpus import Corpus
from ebl.corpus.domain.text import Text, TextId

from ebl.users.domain.user import ApiUser


def update_text(corpus: Corpus, text: Text) -> None:
    user = ApiUser("update_texts.py")
    corpus.update_text(text.id, text, text, user)


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


def update_texts(numbers: Iterable[TextId], id_: int) -> State:
    context = create_context()
    corpus = Corpus(
        context.text_repository,
        context.get_bibliography(),
        context.changelog,
        context.get_transliteration_update_factory(),
    )
    state = State()
    for number in tqdm(numbers, desc=f"Chunk #{id_}", position=id_):
        text = corpus.find(number)
        try:
            update_text(corpus, text)
            state.add_updated()
        except Exception as error:
            state.add_error(error, text)

    return state


def create_chunks(number_of_chunks) -> Iterable[Iterable[TextId]]:
    context = create_context()
    corpus = Corpus(
        context.text_repository,
        context.get_bibliography(),
        context.changelog,
        context.get_transliteration_update_factory(),
    )
    numbers = [text.id for text in corpus.list()]
    chunk_size = math.ceil(len(numbers) / number_of_chunks)
    return pydash.chunk(numbers, chunk_size)


if __name__ == "__main__":
    number_of_jobs = 4
    chunks = create_chunks(number_of_jobs)
    states = Parallel(n_jobs=number_of_jobs)(
        delayed(update_texts)(subset, index) for index, subset in enumerate(chunks)
    )
    final_state = reduce(
        lambda accumulator, state: accumulator.merge(state), states, State()
    )

    with open("invalid_texts.tsv", "w", encoding="utf-8") as file:
        file.write(final_state.to_tsv())

    print("Update texts completed!")
