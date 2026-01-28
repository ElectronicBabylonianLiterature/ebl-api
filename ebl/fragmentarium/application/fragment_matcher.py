from typing import ClassVar, List, Tuple

import attr

from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.application.line_to_vec import LineToVecScore
from ebl.fragmentarium.application.matches.line_to_vec_score import (
    score,
    score_weighted,
)
from ebl.fragmentarium.domain.line_to_vec_encoding import LineToVecEncodings
from ebl.transliteration.domain.museum_number import MuseumNumber


def sort_scores_to_list(results: List[LineToVecScore]) -> List[LineToVecScore]:
    return sorted(results, key=lambda item: -item.score)


@attr.s(auto_attribs=True, frozen=True)
class LineToVecRanking:
    score: List[LineToVecScore]
    score_weighted: List[LineToVecScore]


@attr.s(auto_attribs=True, frozen=True)
class LineToVecRanker:
    NUMBER_OF_RESULTS_TO_RETURN: ClassVar[int] = 15
    _score_results: List[LineToVecScore] = attr.ib(factory=list, init=False)
    _score_weighted_results: List[LineToVecScore] = attr.ib(factory=list, init=False)

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
        score_results.append(line_to_vec_score)


class FragmentMatcher:
    def __init__(self, fragment_repository: FragmentRepository):
        self._fragment_repository = fragment_repository

    def _parse_candidate(self, candidate: str) -> Tuple[LineToVecEncodings, ...]:
        return self._fragment_repository.query_by_museum_number(
            MuseumNumber.of(candidate)
        ).line_to_vec

    def rank_line_to_vec(self, candidate: str) -> LineToVecRanking:
        candidate_line_to_vecs = self._parse_candidate(candidate)
        line_to_vec_entries = (
            self._fragment_repository.query_transliterated_line_to_vec()
        )
        ranker = LineToVecRanker()
        if candidate_line_to_vecs:
            for entry in filter(
                lambda line_to_vec_entry: line_to_vec_entry.museum_number
                != MuseumNumber.of(candidate),
                line_to_vec_entries,
            ):
                line_to_vec_score = LineToVecScore(
                    entry.museum_number,
                    entry.script,
                    score(candidate_line_to_vecs, entry.line_to_vec),
                )
                line_to_vec_weighted_score = LineToVecScore(
                    entry.museum_number,
                    entry.script,
                    score_weighted(candidate_line_to_vecs, entry.line_to_vec),
                )
                ranker.insert_score(line_to_vec_score, line_to_vec_weighted_score)

        return ranker.ranking
