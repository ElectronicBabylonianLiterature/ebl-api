import math
from functools import reduce

import attr
import pydash
from joblib import Parallel, delayed
from tqdm import tqdm

from ebl.app import create_context
from ebl.transliteration.domain.lemmatization import LemmatizationError
from ebl.transliteration.domain.transliteration_error import TransliterationError
from ebl.transliteration.infrastructure.menoizing_sign_repository import (
    MemoizingSignRepository,
)
from ebl.users.domain.user import ApiUser


def update_fragment(transliteration_factory, updater, fragment):
    transliteration = transliteration_factory.create(fragment.text.atf, fragment.notes)
    user = ApiUser("update_fragments.py")
    updater.update_transliteration(fragment.number, transliteration, user)


def find_transliterated(fragment_repository):
    return [fragment.number for fragment in fragment_repository.find_transliterated()]


class State:
    def __init__(self):
        self.invalid_atf = 0
        self.invalid_lemmas = 0
        self.updated = 0
        self.errors = []

    def add_updated(self):
        self.updated += 1

    def add_lemmatization_error(self, error, fragment):
        self.invalid_lemmas += 1
        self.errors.append(f"{fragment.number}\t{error}")

    def add_transliteration_error(self, transliteration_error, fragment):
        self.invalid_atf += 1
        for index, error in enumerate(transliteration_error.errors):
            atf = fragment.text.lines[error["lineNumber"] - 1].atf
            number = fragment.number if index == 0 else len(fragment.number) * " "
            self.errors.append(f"{number}\t{atf}\t{error}")

    def to_tsv(self):
        return "\n".join(
            [
                *self.errors,
                f"# Updated fragments: {self.updated}",
                f"# Invalid ATF: {self.invalid_atf}",
                f"# Invalid lemmas: {self.invalid_lemmas}",
            ]
        )

    def merge(self, other):
        result = State()
        result.invalid_atf = self.invalid_atf + other.invalid_atf
        result.invalid_lemmas = self.invalid_lemmas + other.invalid_lemmas
        result.updated = self.updated + other.updated
        result.errors = self.errors + other.errors
        return result


def update_fragments(numbers, id_, context_factory):
    context = context_factory()
    fragment_repository = context.fragment_repository
    transliteration_factory = context.get_transliteration_update_factory()
    updater = context.get_fragment_updater()
    state = State()

    for number in tqdm(numbers, desc=f"Chuck #{id_}", position=id_):
        fragment = fragment_repository.query_by_fragment_number(number)
        try:
            update_fragment(transliteration_factory, updater, fragment)
            state.add_updated()
        except TransliterationError as error:
            state.add_transliteration_error(error, fragment)
        except LemmatizationError as error:
            state.add_lemmatization_error(error, fragment)

    return state


def create_context_():
    context = create_context()
    context = attr.evolve(
        context, sign_repository=MemoizingSignRepository(context.sign_repository),
    )
    return context


if __name__ == "__main__":
    n_jobs = 4
    numbers = find_transliterated(create_context_().fragment_repository)
    chunks = math.ceil(len(numbers) / n_jobs)
    states = Parallel(n_jobs=n_jobs)(
        delayed(update_fragments)(subset, index, create_context_)
        for index, subset in enumerate(pydash.chunk(numbers, chunks))
    )
    state = reduce(lambda accumulator, state: accumulator.merge(state), states, State())

    with open(f"invalid_fragments.tsv", "w", encoding="utf-8") as file:
        file.write(state.to_tsv())
