import argparse
import math
from functools import reduce
from typing import Callable, Iterable, List, Sequence

import attr
import pydash
from joblib import Parallel, delayed
from tqdm import tqdm

from ebl.app import create_context
from ebl.context import Context
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.application.transliteration_update_factory import (
    TransliterationUpdateFactory,
)
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.lemmatization.domain.lemmatization import LemmatizationError
from ebl.signs.infrastructure.menoizing_sign_repository import MemoizingSignRepository
from ebl.transliteration.domain.transliteration_error import TransliterationError

from ebl.users.domain.user import ApiUser


def update_fragment(
    transliteration_factory: TransliterationUpdateFactory,
    updater: FragmentUpdater,
    fragment: Fragment,
) -> None:
    transliteration = transliteration_factory.create(fragment.text.atf, fragment.notes)
    user = ApiUser("update_fragments.py")
    updater.update_transliteration(fragment.number, transliteration, user, True)


def find_transliterated(fragment_repository: FragmentRepository) -> List[MuseumNumber]:
    return fragment_repository.query_transliterated_numbers()


@attr.s(auto_attribs=True)
class State:
    invalid_atf: int = 0
    invalid_lemmas: int = 0
    invalid_fragment_query: int = 0
    updated: int = 0
    errors: List[str] = attr.ib(factory=list)

    def add_updated(self) -> None:
        self.updated += 1

    def add_error(self, error: Exception, fragment: Fragment) -> None:
        if isinstance(error, LemmatizationError):
            self._add_lemmatization_error(error, fragment)
        elif isinstance(error, TransliterationError):
            self._add_transliteration_error(error, fragment)
        else:
            self._add_error(error, fragment)

    def add_querying_error(self, error: Exception, number: str) -> None:
        self.invalid_fragment_query += 1
        self.errors.append(f"{number}\t\t{error}")

    def _add_lemmatization_error(
        self, error: LemmatizationError, fragment: Fragment
    ) -> None:
        self.invalid_lemmas += 1
        self.errors.append(f"{fragment.number}\t{error}")

    def _add_transliteration_error(
        self, error: TransliterationError, fragment: Fragment
    ) -> None:
        self.invalid_atf += 1
        for index, error in enumerate(error.errors):
            atf = fragment.text.lines[error["lineNumber"] - 1].atf
            number = fragment.number if index == 0 else len(str(fragment.number)) * " "
            self.errors.append(f"{number}\t{atf}\t{error}")

    def _add_error(self, error: Exception, fragment: Fragment) -> None:
        self.invalid_atf += 1
        self.errors.append(f"{fragment.number}\t\t{error}")

    def to_tsv(self) -> str:
        return "\n".join(
            [
                *self.errors,
                f"# Updated fragments: {self.updated}",
                f"# Invalid ATF: {self.invalid_atf}",
                f"# Invalid lemmas: {self.invalid_lemmas}",
                f"# Invalid fragment querys: {self.invalid_fragment_query}",
            ]
        )

    def merge(self, other: "State") -> "State":
        return State(
            self.invalid_atf + other.invalid_atf,
            self.invalid_lemmas + other.invalid_lemmas,
            self.invalid_fragment_query + other.invalid_fragment_query,
            self.updated + other.updated,
            self.errors + other.errors,
        )


def update_fragments(
    numbers: Iterable[MuseumNumber], id_: int, context_factory: Callable[[], Context]
) -> State:
    context = context_factory()
    fragment_repository = context.fragment_repository
    transliteration_factory = context.get_transliteration_update_factory()
    updater = context.get_fragment_updater()
    state = State()
    for number in tqdm(numbers, desc=f"Chunk #{id_}", position=id_):
        try:
            fragment = fragment_repository.query_by_museum_number(number)
            try:
                update_fragment(transliteration_factory, updater, fragment)
                state.add_updated()
            except Exception as error:
                state.add_error(error, fragment)
        except Exception as error:
            state.add_querying_error(error, number)

    return state


def create_context_() -> Context:
    context = create_context()
    context = attr.evolve(
        context, sign_repository=MemoizingSignRepository(context.sign_repository)
    )
    return context


def create_chunks(number_of_chunks) -> Sequence[Sequence[str]]:
    numbers = find_transliterated(create_context_().fragment_repository)
    chunk_size = math.ceil(len(numbers) / number_of_chunks)
    return pydash.chunk(numbers, chunk_size)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-w", "--workers", type=int, help="Number of threads to perform migration"
    )
    args = parser.parse_args()
    workers = args.workers or 6

    chunks = create_chunks(workers)
    states = Parallel(n_jobs=workers)(
        delayed(update_fragments)(subset, index, create_context_)
        for index, subset in enumerate(chunks)
    )
    final_state = reduce(
        lambda accumulator, state: accumulator.merge(state), states, State()
    )

    with open("invalid_fragments.tsv", "w", encoding="utf-8") as file:
        file.write(final_state.to_tsv())

    print("Update fragments completed!")
