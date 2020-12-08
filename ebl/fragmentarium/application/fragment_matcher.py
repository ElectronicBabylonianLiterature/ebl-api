from collections import OrderedDict
from typing import Tuple, Union, List

import attr
from singledispatchmethod import singledispatchmethod  # pyre-ignore[21]

from ebl.fragmentarium.application.matches.create_line_to_vec import (
    LineToVecEncoding,
    LineToVecEncodings,
)
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.application.matches.line_to_vec_score import (
    score,
    score_weighted,
)
from ebl.fragmentarium.domain.museum_number import MuseumNumber


@attr.s(auto_attribs=True, frozen=True)
class LineToVecRanking:
    score: List[Tuple[str, int]]
    score_weighted: List[Tuple[str, int]]


class FragmentMatcher:
    def __init__(self, fragment_repository: FragmentRepository):

        self.fragment_repository = fragment_repository
        self._fragment_repository = fragment_repository

    @singledispatchmethod  # pyre-ignore[56]
    def parse_candidate(self, candidate) -> Tuple[LineToVecEncodings, ...]:
        return (LineToVecEncoding.from_list(candidate),)

    @parse_candidate.register(str)  # pyre-ignore[56]
    def _parse_candidate_str(self, candidate: str) -> Tuple[LineToVecEncodings, ...]:
        line_to_vec = self.fragment_repository.query_by_museum_number(
            MuseumNumber.of(candidate)
        ).line_to_vec
        if line_to_vec:
            return tuple(line_to_vec)
        else:
            raise ValueError("Fragment has no line to vec")

    def _sort_dict_desc(self, score: dict) -> OrderedDict:
        return OrderedDict(sorted(score.items(), key=lambda item: -item[1]))

    def rank_line_to_vec(
        self, candidate: Union[str, Tuple[int, ...]]
    ) -> LineToVecRanking:
        candidates = self.parse_candidate(candidate)
        score_results = dict()
        score_weighted_results = dict()
        fragments = self.fragment_repository.query_transliterated_line_to_vec()

        for candidate in candidates:
            for fragment_id, line_to_vecs in fragments.items():
                for line_to_vec in line_to_vecs:
                    score_result = score(candidate, line_to_vec)
                    if score_result > score_results.get(fragment_id, -1):
                        score_results[fragment_id] = score_result
                    score_result_weighted = score_weighted(candidate, line_to_vec)
                    if score_result_weighted > score_weighted_results.get(
                        fragment_id, -1
                    ):
                        score_weighted_results[fragment_id] = score_result_weighted

        number_of_results_to_return = 15
        return LineToVecRanking(
            score=list(self._sort_dict_desc(score_results).items())[
                :number_of_results_to_return
            ],
            score_weighted=list(self._sort_dict_desc(score_weighted_results).items())[
                :number_of_results_to_return
            ],
        )
