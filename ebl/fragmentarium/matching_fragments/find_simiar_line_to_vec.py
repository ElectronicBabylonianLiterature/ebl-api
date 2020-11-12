import math
from typing import Callable, Iterable, List, Sequence

import attr
import pydash  # pyre-ignore
from dotenv import load_dotenv
from joblib import Parallel, delayed  # pyre-ignore
from tqdm import tqdm  # pyre-ignore

from ebl.app import create_context
from ebl.context import Context
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.fragmentarium.matching_fragments.score import matching_subseq, \
    matching_subseq_w
from ebl.transliteration.infrastructure.menoizing_sign_repository import (
    MemoizingSignRepository,
)

load_dotenv()





def update_fragments(
    fragmentNumber: str, numbers: Iterable[MuseumNumber], id_: int, context_factory: Callable[[], Context]
):

    context = context_factory()
    fragment_repository = context.fragment_repository

    unweighted_score_results = dict()
    weighted_score_results = dict()
    fragment_2 = fragment_repository.query_by_museum_number(
        MuseumNumber.of(fragmentNumber))
    for number in tqdm(numbers, desc=f"Chunk #{id_}", position=id_):
        fragment = fragment_repository.query_by_museum_number(number)
        score = matching_subseq(fragment.line_to_vec.line_to_vec, fragment_2.line_to_vec.line_to_vec)
        weighted_score = matching_subseq_w(fragment.line_to_vec.line_to_vec, fragment_2.line_to_vec.line_to_vec)
        unweighted_score_results[str(fragment.number)] = score
        weighted_score_results[str(fragment.number)] = weighted_score

    return unweighted_score_results, weighted_score_results


def create_context_() -> Context:
    context = create_context()
    context = attr.evolve(
        context, sign_repository=MemoizingSignRepository(context.sign_repository)
    )
    return context





if __name__ == "__main__":
    fragmentId = "K.8981"
    number_of_jobs = 16
    context = create_context()
    line_to_vecs = context.line_to_vec_repository.get_line_to_vec_with_rulings()
    match_candidate = line_to_vecs[fragmentId]
    final_unweighted = dict()
    final_weighted = dict()
    for k, v in line_to_vecs.items():
        final_unweighted[k] = matching_subseq(match_candidate.line_to_vec,
                                              v.line_to_vec)
        final_weighted[k] = matching_subseq_w(match_candidate.line_to_vec, v.line_to_vec)

    final_unweighted = {k: v for k, v in
                        sorted(final_unweighted.items(), key=lambda item: -item[1]) if
                        v != 0}
    final_weighted = {k: v for k, v in
                      sorted(final_weighted.items(), key=lambda item: -item[1]) if
                      v != 0}

    with open(f"results/{fragmentId}_scores.tsv", "w", encoding="utf-8") as file:
        file.write(f"{fragmentId} Score:\t\t\tWeighted Score:\n\n")
        for k, v in zip(list(final_unweighted.items())[:30], list(final_weighted.items())[:30]):
            file.write(f"{k[0]},{k[1]}\t\t\t\t")
            file.write(f"{v[0]},{v[1]}\n")
