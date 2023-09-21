from typing import Union, Dict, Sequence


def flatten_field(input_: Union[str, Dict], depth=1) -> Dict:
    return {
        "$reduce": {
            "input": flatten_field(input_, depth=depth - 1) if depth > 1 else input_,
            "initialValue": [],
            "in": {"$concatArrays": ["$$value", "$$this"]},
        }
    }


def drop_duplicates(input_: Union[str, Dict]) -> Dict:
    return {"$setUnion": [input_, []]}


def ngrams(input_: Union[str, Dict], n: int) -> Dict:
    if n <= 0:
        raise ValueError("ngram size must be 1 or more")
    return {
        "$zip": {
            "inputs": [
                input_,
                *(
                    {
                        "$slice": [
                            input_,
                            i + 1,
                            {"$size": input_},
                        ]
                    }
                    for i in range(n - 1)
                ),
            ]
        }
    }


def filter_array(input_, as_, cond) -> Dict:
    return {"$filter": {"input": input_, "as": as_, "cond": cond}}


def add_ngram_field(
    input_: Union[str, Dict],
    N: Sequence[int],
    output_: str = "ngrams",
):
    signs_to_exclude = ["X", ""]

    exclude_empty = {
        "$eq": [
            {
                "$size": {
                    "$setIntersection": [
                        "$$this",
                        signs_to_exclude,
                    ]
                }
            },
            0,
        ]
    }
    return {
        "$addFields": {
            output_: drop_duplicates(
                filter_array(
                    {"$concatArrays": [ngrams(input_, n) for n in N if n > 0]},
                    "this",
                    exclude_empty,
                )
            )
        }
    }


def replace_all(input_: Union[str, Dict], old: str, new: str):
    return {
        "$replaceAll": {
            "input": input_,
            "find": old,
            "replacement": new,
        }
    }
