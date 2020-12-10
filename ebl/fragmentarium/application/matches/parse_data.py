import csv
import itertools
from collections import OrderedDict
from typing import Dict, Generator, Tuple

import pydash  # pyre-ignore[21]
from dotenv import load_dotenv  # pyre-ignore[21]
from tqdm import tqdm  # pyre-ignore

from ebl.app import create_context
from ebl.fragmentarium.application.fragment_matcher import FragmentMatcher, Scores
from ebl.fragmentarium.application.matches.create_line_to_vec import (
    LineToVecEncoding,
)
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.users.domain.user import ApiUser

load_dotenv()


def seq_to_ints(sequence: str) -> Tuple[int, ...]:
    return tuple([int(sequence[i]) for i in range(0, len(sequence))])


with open("testData.csv") as test_data:
    test_data = list(csv.reader(test_data, delimiter="\t"))

formatted_test_data = []
for entry in test_data[1:]:
    fragment_ids = entry[0].split(",")
    line_to_vec_encodings = tuple(
        [
            tuple(
                [
                    seq_to_ints(split_item)
                    for split_item in line_to_vec_encoding.split("-")
                ]
            )
            for line_to_vec_encoding in entry[1].split(",")
        ]
    )

    excluded = entry[2].split(",") if len(entry) == 3 else []
    if len(fragment_ids) != len(line_to_vec_encodings):
        raise ValueError(f"Something wrong with the data {fragment_ids}")
    matches = dict()
    match = dict()
    for id, seqs in zip(fragment_ids, line_to_vec_encodings):
        match[id] = seqs
    matches["match"] = match
    matches["excluded"] = excluded
    formatted_test_data.append(matches)

print(formatted_test_data)


def grid_search(step: int) -> Generator[Dict[LineToVecEncoding, int], None, None]:
    weightings = OrderedDict({encoding: None for encoding in LineToVecEncoding})
    grid = [list(range(0, 101, step)) for _ in list(weightings.keys())]

    for current_weights in itertools.product(
       *grid
    ):
        yield {
            list(weightings.keys())[i]: current_weights[i]
            for i in range(len(current_weights))
        }


def squared_distance(fragment_id: str, weighted_score: Scores) -> int:
    return pydash.find_index(weighted_score, lambda x: x[0] == fragment_id) ** 2


if __name__ == "__main__":
    context = create_context()
    fragment_matcher = FragmentMatcher(context.fragment_repository)
    updater = context.get_fragment_updater()
    transliteration_factory = context.get_transliteration_update_factory()
    user = ApiUser("update_fragments.py")
    updater.update_transliteration(
        MuseumNumber.of("CBS.589"), transliteration_factory.create(""), user
    )

    x = list(grid_search(50))
    best_candidate = dict()
    for weights in tqdm(grid_search(step=50)):
        sum_squared_distances = 0
        counter = 0
        for match in formatted_test_data:
            for elem, sequence in match["match"].items():
                ranking = fragment_matcher.rank_line_to_vec(
                    sequence,
                    [elem, *match["excluded"]],
                    weights,
                )
                counter += 1
                sum_squared_distances += squared_distance(elem, ranking.score_weighted)
        error = sum_squared_distances / counter
        best_candidate[frozenset(weights.items())] = error

    best_candidate = sorted(best_candidate.items(), key=lambda item: item[1])
    for candidate in best_candidate[:10]:
        print(candidate)
