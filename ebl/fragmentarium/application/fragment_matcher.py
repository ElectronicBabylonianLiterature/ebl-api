from typing import ClassVar, Tuple, List

import attr
import pydash

from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.application.line_to_vec import LineToVecScore
from ebl.fragmentarium.application.matches.line_to_vec_score import (
    score,
    score_weighted,
)
from ebl.fragmentarium.domain.line_to_vec_encoding import LineToVecEncodings
from ebl.fragmentarium.domain.museum_number import MuseumNumber


def sort_scores_to_list(results: List[LineToVecScore]) -> List[LineToVecScore]:
    return sorted(results, key=lambda item: -item.score)


@attr.s(auto_attribs=True, frozen=True)
class LineToVecRanking:
    score: List[LineToVecScore]
    score_weighted: List[LineToVecScore]


@attr.s(auto_attribs=True, frozen=True)
class LineToVecRanker:
    NUMBER_OF_RESULTS_TO_RETURN: ClassVar[int] = 15
    _score_results: List[LineToVecScore] = []
    _score_weighted_results: List[LineToVecScore] = []

    @property
    def score(self) -> List[LineToVecScore]:
        return sort_scores_to_list(self._score_results)[
            : LineToVecRanker.NUMBER_OF_RESULTS_TO_RETURN
        ]

    @property
    def score_weighted(self) -> List[LineToVecScore]:
        return sort_scores_to_list(self._score_weighted_results)[
            : LineToVecRanker.NUMBER_OF_RESULTS_TO_RETURN
        ]

    @property
    def ranking(self) -> LineToVecRanking:
        return LineToVecRanking(self.score, self.score_weighted)

    def insert_score(
        self,
        line_to_vec_score: LineToVecScore,
        line_to_vec_score_weighted: LineToVecScore,
    ) -> None:
        self._insert_score(line_to_vec_score, self._score_results)
        self._insert_score(line_to_vec_score_weighted, self._score_weighted_results)

    def _insert_score(
        self, line_to_vec_score: LineToVecScore, score_results: List[LineToVecScore]
    ) -> None:
        previous_score = pydash.find(score_results, line_to_vec_score.id)
        if line_to_vec_score not in score_results or line_to_vec_score.score > (
            previous_score.score if previous_score else -1
        ):
            score_results.append(line_to_vec_score)


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
        line_to_vec_entries = (
            self.fragment_repository.query_transliterated_line_to_vec()
        )
        ranker = LineToVecRanker()

        for entry in filter(
            lambda x: x.id != MuseumNumber.of(candidate), line_to_vec_entries
        ):
            line_to_vec_score = LineToVecScore(
                entry.id, entry.script, score(candidate_line_to_vecs, entry.line_to_vec)
            )
            line_to_vec_weighted_score = LineToVecScore(
                entry.id,
                entry.script,
                score_weighted(candidate_line_to_vecs, entry.line_to_vec),
            )
            ranker.insert_score(line_to_vec_score, line_to_vec_weighted_score)

        return ranker.ranking
