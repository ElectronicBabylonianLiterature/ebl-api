import math
from typing import Callable, Iterable, List, Sequence

import pydash  # pyre-ignore
from dotenv import load_dotenv
from joblib import Parallel, delayed  # pyre-ignore
from tqdm import tqdm  # pyre-ignore

from ebl.app import create_context
from ebl.context import Context
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.domain.museum_number import MuseumNumber

load_dotenv()


def find_transliterated(fragment_repository: FragmentRepository) -> List[MuseumNumber]:
    return fragment_repository.query_transliterated_numbers()


def update_fragments(
    numbers: Iterable[MuseumNumber], id_: int, context_factory: Callable[[], Context]
):

    context = context_factory()
    fragment_repository = context.fragment_repository
    line_to_vec = dict()
    for number in tqdm(numbers, desc=f"Chunk #{id_}", position=id_):
        fragment = fragment_repository.query_by_museum_number(number)
        line_to_vec[str(fragment.number)] = fragment.line_to_vec

    return line_to_vec


def create_context_() -> Context:
    context = create_context()
    return context


def create_chunks(number_of_chunks) -> Sequence[Sequence[str]]:
    numbers = find_transliterated(create_context_().fragment_repository)
    chunk_size = math.ceil(len(numbers) / number_of_chunks)
    return pydash.chunk(numbers, chunk_size)


if __name__ == "__main__":
    number_of_jobs = 16
    chunks = create_chunks(number_of_jobs)
    states = Parallel(n_jobs=number_of_jobs, prefer="processes")(
        delayed(update_fragments)(subset, index, create_context_)
        for index, subset in enumerate(chunks)
    )
    final_state = dict()
    for state in states:
        for key, value in state.items():
            final_state[key] = value
    context = create_context_()

    context.line_to_vec_repository.insert_all(final_state)


