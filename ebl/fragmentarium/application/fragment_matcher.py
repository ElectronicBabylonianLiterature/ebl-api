import itertools
from typing import ClassVar, Tuple, List, Dict

import attr

from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.application.matches.line_to_vec_score import (
    score,
    score_weighted,
)
from ebl.fragmentarium.domain.line_to_vec_encoding import (
    LineToVecEncodings,
)
from ebl.fragmentarium.domain.museum_number import MuseumNumber

Scores = List[Tuple[str, int]]
Results = Dict[str, int]


def sort_scores_to_list(results: Results) -> Scores:
    return sorted(results.items(), key=lambda item: -item[1])


@attr.s(auto_attribs=True, frozen=True)
class LineToVecRanking:
    score: Scores
    score_weighted: Scores


@attr.s(auto_attribs=True, frozen=True)
class LineToVecRanker:
    NUMBER_OF_RESULTS_TO_RETURN: ClassVar[int] = 15
    _score_results: Results = attr.ib(factory=dict, init=False)
    _score_weighted_results: Results = attr.ib(factory=dict, init=False)

    @property
    def score(self) -> Scores:
        return sort_scores_to_list(self._score_results)[
            : LineToVecRanker.NUMBER_OF_RESULTS_TO_RETURN
        ]

    @property
    def score_weighted(self) -> Scores:
        return sort_scores_to_list(self._score_weighted_results)[
            : LineToVecRanker.NUMBER_OF_RESULTS_TO_RETURN
        ]

    @property
    def ranking(self) -> LineToVecRanking:
        return LineToVecRanking(self.score, self.score_weighted)

    def insert_score(self, fragment_id: str, score: int, score_weighted: int) -> None:
        self._insert_score(fragment_id, score, self._score_results)
        self._insert_score(fragment_id, score_weighted, self._score_weighted_results)

    def _insert_score(
        self, fragment_id: str, score_result: int, score_results: Dict[str, int]
    ) -> None:
        if (
            fragment_id not in score_results
            or score_result > score_results[fragment_id]
        ):
            score_results[fragment_id] = score_result


class FragmentMatcher:
    def __init__(self, fragment_repository: FragmentRepository):
        self.fragment_repository = fragment_repository
        self._fragment_repository = fragment_repository

    def _parse_candidate(self, candidate: str) -> Tuple[LineToVecEncodings, ...]:
        line_to_vec = self.fragment_repository.query_by_museum_number(
            MuseumNumber.of(candidate)
        ).line_to_vec
        if line_to_vec:
            return tuple(line_to_vec)
        else:
            raise ValueError("Fragment has no line to vec")

    def rank_line_to_vec(self, candidate: str) -> LineToVecRanking:
        candidate_line_to_vecs = self._parse_candidate(candidate)
        fragments = self.fragment_repository.query_transliterated_line_to_vec()
        ranker = LineToVecRanker()

        for candidate_line_to_vec, fragment in itertools.product(
            candidate_line_to_vecs,
            list(filter(lambda x: x[0] != candidate, fragments.items())),
        ):
            fragment_id, line_to_vecs = fragment
            for line_to_vec in line_to_vecs:
                ranker.insert_score(
                    fragment_id,
                    score(candidate_line_to_vec, line_to_vec),
                    score_weighted(candidate_line_to_vec, line_to_vec),
                )

        return ranker.ranking
