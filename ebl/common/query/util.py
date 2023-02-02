from typing import Union, Dict


def flatten_field(input_: Union[str, Dict]) -> Dict:
    return {
        "$reduce": {
            "input": input_,
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
