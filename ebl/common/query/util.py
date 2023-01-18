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
