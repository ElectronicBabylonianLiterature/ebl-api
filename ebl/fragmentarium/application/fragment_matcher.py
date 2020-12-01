from functools import singledispatch
from typing import Tuple, Union, List, Dict

from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.domain.fragment import LineToVecEncoding, LineToVecEncodings
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.fragmentarium.application.line_to_vec_score import score, score_weighted


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

    def line_to_vec(
        self, candidate: Union[str, Tuple[int, ...]]
    ) -> Dict[str, List[Tuple[str, str]]]:
        candidate_line_to_vec = self.parse_candidate(candidate)
        score_results = dict()
        score_weighted_results = dict()
        fragments = self.fragment_repository.query_transliterated_line_to_vec()

        for fragment_id, line_to_vec in fragments.items():
            score_results[fragment_id] = score(candidate_line_to_vec, line_to_vec)
            score_weighted_results[fragment_id] = score_weighted(
                candidate_line_to_vec, line_to_vec
            )

        return {
            "score": list(self._sort_dict_desc(score_results).items())[:15],
            "score_weighted": list(
                self._sort_dict_desc(score_weighted_results).items()
            )[:15],
        }
