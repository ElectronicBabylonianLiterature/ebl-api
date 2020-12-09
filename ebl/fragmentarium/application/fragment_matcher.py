from collections import OrderedDict
from typing import ClassVar, Tuple, Union, List, Dict

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


Scores = List[Tuple[str, int]]
Results = Dict[str, int]


def sort_dict_desc(score: Results) -> OrderedDict:
    return OrderedDict(sorted(score.items(), key=lambda item: -item[1]))


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
        return list(sort_dict_desc(self._score_results).items())[
            : LineToVecRanker.NUMBER_OF_RESULTS_TO_RETURN
        ]

    @property
    def score_weighted(self) -> Scores:
        return list(sort_dict_desc(self._score_weighted_results).items())[
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
        if score_result > score_results.get(fragment_id, -1):
            score_results[fragment_id] = score_result


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

    def rank_line_to_vec(
        self, candidate: Union[str, Tuple[int, ...]]
    ) -> LineToVecRanking:
        candidates = self.parse_candidate(candidate)
        fragments = self.fragment_repository.query_transliterated_line_to_vec()
        ranker = LineToVecRanker()

        for candidate in candidates:
            for fragment_id, line_to_vecs in fragments.items():
                for line_to_vec in line_to_vecs:
                    ranker.insert_score(
                        fragment_id,
                        score(candidate, line_to_vec),
                        score_weighted(candidate, line_to_vec),
                    )

        return ranker.ranking
