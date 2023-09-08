from typing import Optional, Sequence, Union, Dict

from ebl.common.query.util import drop_duplicates, filter_array, ngrams
from ebl.corpus.domain.chapter import ChapterId
from ebl.corpus.infrastructure.queries import chapter_id_query

NGRAM_FIELD = "ngram"


def aggregate_all_ngrams(
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


def aggregate_fragment_ngrams(
    number: str, N: Sequence[int], signs_to_exclude: Optional[Sequence[str]] = None
):
    return [
        {"$match": {"_id": number}},
        {"$project": {NGRAM_FIELD: {"$split": ["$signs", " "]}}},
        *aggregate_all_ngrams(f"${NGRAM_FIELD}", N, NGRAM_FIELD, signs_to_exclude),
    ]


def aggregate_chapter_ngrams(
    chapter_id: ChapterId,
    N: Sequence[int],
    linebreak_char="#",
    signs_to_exclude: Optional[Sequence[str]] = None,
):
    replace_linebreaks = {
        "$replaceAll": {
            "input": "$signs",
            "find": "\n",
            "replacement": f" {linebreak_char} ",
        }
    }

    return [
        {"$match": chapter_id_query(chapter_id)},
        {"$project": {"signs": 1}},
        {"$unwind": "$signs"},
        {
            "$project": {
                NGRAM_FIELD: {
                    "$split": [
                        replace_linebreaks,
                        " ",
                    ]
                }
            }
        },
        *aggregate_all_ngrams(f"${NGRAM_FIELD}", N, NGRAM_FIELD, signs_to_exclude),
        {"$unwind": f"${NGRAM_FIELD}"},
        {"$group": {"_id": None, NGRAM_FIELD: {"$addToSet": f"${NGRAM_FIELD}"}}},
        {"$project": {"_id": False}},
    ]
