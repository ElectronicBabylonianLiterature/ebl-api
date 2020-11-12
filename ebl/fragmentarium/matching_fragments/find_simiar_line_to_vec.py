import attr

from ebl.app import create_context
from ebl.context import Context
from ebl.fragmentarium.matching_fragments.score import score, score_weighted
from ebl.transliteration.infrastructure.menoizing_sign_repository import (
    MemoizingSignRepository,
)


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
        final_unweighted[k] = score(match_candidate.line_to_vec, v.line_to_vec)
        final_weighted[k] = score_weighted(match_candidate.line_to_vec, v.line_to_vec)

    final_unweighted = {
        k: v
        for k, v in sorted(final_unweighted.items(), key=lambda item: -item[1])
        if v != 0
    }
    final_weighted = {
        k: v
        for k, v in sorted(final_weighted.items(), key=lambda item: -item[1])
        if v != 0
    }

    with open(f"results/{fragmentId}_scores.tsv", "w", encoding="utf-8") as file:
        file.write(f"{fragmentId} Score:\t\t\tWeighted Score:\n\n")
        for k, v in zip(
            list(final_unweighted.items())[:30], list(final_weighted.items())[:30]
        ):
            file.write(f"{k[0]},{k[1]}\t\t\t\t")
            file.write(f"{v[0]},{v[1]}\n")
