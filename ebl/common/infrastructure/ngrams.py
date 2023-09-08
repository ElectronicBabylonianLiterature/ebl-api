from typing import Optional, Sequence, Union, Dict

from ebl.common.query.util import drop_duplicates, filter_array, ngrams

NGRAM_FIELD = "ngram"


def create_all_ngrams(
    input_: Union[str, Dict],
    N: Sequence[int],
    output_: str = "ngrams",
    signs_to_exclude: Optional[Sequence[str]] = None,
):
    if signs_to_exclude is None:
        signs_to_exclude = ["X", ""]

    no_empty_signs = {
        "$eq": [
            {
                "$size": {
                    "$setIntersection": [
                        f"$${NGRAM_FIELD}",
                        signs_to_exclude,
                    ]
                }
            },
            0,
        ]
    }
    return [
        {
            "$addFields": {
                output_: drop_duplicates(
                    filter_array(
                        {"$concatArrays": [ngrams(input_, n) for n in N if n > 0]},
                        NGRAM_FIELD,
                        no_empty_signs,
                    )
                )
            }
        },
    ]


def create_fragment_ngrams(
    number: str, N: Sequence[int], signs_to_exclude: Optional[Sequence[str]] = None
):
    return [
        {"$match": {"_id": number}},
        {"$project": {NGRAM_FIELD: {"$split": ["$signs", " "]}}},
        *create_all_ngrams(f"${NGRAM_FIELD}", N, NGRAM_FIELD, signs_to_exclude),
    ]


def create_chapter_ngrams():
    pass
