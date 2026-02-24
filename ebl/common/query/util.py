from typing import Union, Dict, Optional, List
from ebl.transliteration.domain.museum_number import (
    PREFIX_ORDER,
    NUMBER_PREFIX_ORDER,
    DEFAULT_PREFIX_ORDER,
)


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


def ngrams(input_: Union[str, Dict], n) -> Dict:
    if n <= 1:
        raise ValueError("ngram size must be 2 or more")
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


def convert_to_int(input_: Union[str, dict], default=0) -> dict:
    return {"$convert": {"input": input_, "to": "int", "onError": default}}


def sort_by_museum_number(
    pre_sort_keys: Optional[dict] = None, post_sort_keys: Optional[dict] = None
) -> List[Dict]:
    sort_keys = [
        {
            "$cond": [
                {
                    "$regexMatch": {
                        "input": "$museumNumber.prefix",
                        "regex": r"^\d+$",
                    }
                },
                NUMBER_PREFIX_ORDER,
                {
                    "$switch": {
                        "branches": [
                            {
                                "case": {"$eq": ["$museumNumber.prefix", key]},
                                "then": value,
                            }
                            for key, value in PREFIX_ORDER.items()
                        ],
                        "default": DEFAULT_PREFIX_ORDER,
                    }
                },
            ]
        },
        convert_to_int("$museumNumber.prefix", 0),
        "$museumNumber.prefix",
        convert_to_int("$museumNumber.number", default=float("Inf")),
        "$museumNumber.number",
        convert_to_int("$museumNumber.suffix", default=float("Inf")),
        "$museumNumber.suffix",
    ]
    return [
        {"$addFields": {"tmpSortKeys": sort_keys}},
        {
            "$sort": {
                **(pre_sort_keys or {}),
                **{f"tmpSortKeys.{i}": 1 for i in range(len(sort_keys))},
                **(post_sort_keys or {}),
            }
        },
        {"$project": {"tmpSortKeys": False}},
    ]
