from functools import singledispatch
from typing import Tuple, Union, List

import attr

from ebl.fragmentarium.application.create_line_to_vec import (
    LineToVecEncoding,
    LineToVecEncodings,
)
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.application.line_to_vec_score import score, score_weighted
from ebl.fragmentarium.domain.museum_number import MuseumNumber


@attr.s(auto_attribs=True, frozen=True)
class LineToVecRanking:
    score: List[Tuple[str, int]]
    score_weighted: List[Tuple[str, int]]


class FragmentMatcher:
    def __init__(self, fragment_repository: FragmentRepository):

        self.fragment_repository = fragment_repository
        self._fragment_repository = fragment_repository
        self.parse_candidate = singledispatch(self.parse_candidate)  # pyre-ignore[8]
        self.parse_candidate.register(str, self._parse_candidate_str)

    def parse_candidate(self, candidate) -> LineToVecEncodings:
        return LineToVecEncoding.from_list(candidate)

    def _parse_candidate_str(self, candidate: str) -> LineToVecEncodings:
        line_to_vec = self.fragment_repository.query_by_museum_number(
            MuseumNumber.of(candidate)
        ).line_to_vec
        if line_to_vec:
            return line_to_vec
        else:
            raise ValueError("Fragment has no line to vec")

    def _sort_dict_desc(self, score: dict) -> dict:
        return {k: v for k, v in sorted(score.items(), key=lambda item: -item[1])}

    def rank_line_to_vec(
        self, candidate: Union[str, Tuple[int, ...]]
    ) -> LineToVecRanking:
        candidate_line_to_vec = self.parse_candidate(candidate)
        score_results = dict()
        score_weighted_results = dict()
        fragments = self.fragment_repository.query_transliterated_line_to_vec()

        for fragment_id, line_to_vec in fragments.items():
            score_results[fragment_id] = score(candidate_line_to_vec, line_to_vec)
            score_weighted_results[fragment_id] = score_weighted(
                candidate_line_to_vec, line_to_vec
            )

        return LineToVecRanking(
            score=list(self._sort_dict_desc(score_results).items())[:15],
            score_weighted=list(self._sort_dict_desc(score_weighted_results).items())[
                :15
            ],
        )
