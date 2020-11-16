import attr
from dotenv import load_dotenv  # pyre-ignore[21]

from ebl.app import create_context
from ebl.context import Context
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.fragmentarium.matching_fragments.score import score, score_weighted
from ebl.transliteration.infrastructure.menoizing_sign_repository import (
    MemoizingSignRepository,
)

load_dotenv()


def create_context_() -> Context:
    context = create_context()
    context = attr.evolve(
        context, sign_repository=MemoizingSignRepository(context.sign_repository)
    )
    return context


def sort(score: dict) -> dict:
    return {k: v for k, v in sorted(score.items(), key=lambda item: -item[1])}


if __name__ == "__main__":
    candidate_fragment_id = "K.8981"

    context = create_context()
    candidate = context.fragment_repository.query_by_museum_number(
        MuseumNumber.of(candidate_fragment_id)
    )
    score_results = dict()
    score_weighted_results = dict()
    fragments = context.fragment_repository.query_transliterated_line_to_vec()

    for fragment in fragments:
        for fragment_id, line_to_vec in fragment.items():
            score_results[fragment_id] = score(
                candidate.line_to_vec.line_to_vec, line_to_vec.line_to_vec
            )
            score_weighted_results[fragment_id] = score_weighted(
                candidate.line_to_vec.line_to_vec, line_to_vec.line_to_vec
            )

    with open(
        f"results/{candidate_fragment_id}_scores_.tsv", "w", encoding="utf-8"
    ) as file:
        file.write("Ranking for line to vec score of the best 30 fragments\n")
        file.write(f"{candidate_fragment_id}\n{'Score': <22}Weighted Score\n\n")
        for k, v in zip(
            list(sort(score_results).items())[:30],
            list(sort(score_weighted_results).items())[:30],
        ):
            file.write(f"{k[0]: <15},{k[1]: <7}")
            file.write(f"{v[0]: <15},{v[1]: <7}\n")

    print("Ranking complete")
