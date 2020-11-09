import math
import random
from typing import Callable, Iterable, List, Sequence

import attr
import pydash  # pyre-ignore
from joblib import Parallel, delayed  # pyre-ignore
from tqdm import tqdm  # pyre-ignore

from ebl.app import create_context
from ebl.context import Context
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.matching_fragments.line_to_vec_updater import \
    calculate_all_metrics
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.transliteration.infrastructure.menoizing_sign_repository import (
    MemoizingSignRepository,
)

from dotenv import load_dotenv
load_dotenv()


def find_transliterated(fragment_repository: FragmentRepository) -> List[MuseumNumber]:
    return fragment_repository.query_transliterated_numbers()


def update_fragments(
    numbers: Iterable[MuseumNumber], id_: int, context_factory: Callable[[], Context]
):
    context = context_factory()
    fragment_repository = context.fragment_repository
    dict_of_distances = {}
    for number_1, number_2 in tqdm(zip(numbers[: len(numbers)//2], numbers[len(numbers)//2:])):
        fragment_1 = fragment_repository.query_by_museum_number(number_1)
        fragment_2 = fragment_repository.query_by_museum_number(number_2)
        metrics_score = calculate_all_metrics("".join(map(str, fragment_1.line_to_vec)),
                                              "".join(map(str, fragment_2.line_to_vec)))

        for metric in metrics_score.keys():
            if metric in dict_of_distances:
                dict_of_distances[metric].append(metrics_score[metric])
            else:
                dict_of_distances[metric] = [metrics_score[metric]]
    return dict_of_distances


def create_context_() -> Context:
    context = create_context()
    context = attr.evolve(
        context, sign_repository=MemoizingSignRepository(context.sign_repository)
    )
    return context


def create_chunks(number_of_chunks) -> Sequence[Sequence[str]]:
    numbers = find_transliterated(create_context_().fragment_repository)
    random.Random(4).shuffle(numbers)
    chunk_size = math.ceil(len(numbers) / number_of_chunks)
    return pydash.chunk(numbers, chunk_size)


if __name__ == "__main__":
    number_of_jobs = 16
    chunks = create_chunks(number_of_jobs)
    states = Parallel(n_jobs=number_of_jobs, prefer="processes")(
        delayed(update_fragments)(subset, index, create_context_)
        for index, subset in enumerate(chunks)
    )
    final_state = states[0]
    for state in states:
        for metrics in state.keys():
            final_state[metrics].extend(state[metrics])

    for key, item in final_state.items():
        final_state[key] = round(sum(item) / len(item), 2)

    with open("results/distances.tsv", "w", encoding="utf-8") as file:
        file.write(",".join(map(str, final_state.keys())))
        file.write("\n")
        file.write(",".join(map(str, final_state.values())))

    print("Update fragments completed!")
