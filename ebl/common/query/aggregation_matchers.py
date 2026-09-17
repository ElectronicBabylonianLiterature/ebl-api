from typing import Dict, Sequence, Tuple

FieldVariablePairs = Sequence[Tuple[str, str]]


def match_all(pairs: FieldVariablePairs) -> Dict:
    return {
        "$match": {
            "$expr": {"$and": [{"$eq": [field, variable]} for field, variable in pairs]}
        }
    }


def text_id_pairs(field_prefix: str, variable_prefix: str) -> FieldVariablePairs:
    return [
        (f"{field_prefix}{part}", f"{variable_prefix}{part}")
        for part in ("genre", "category", "index")
    ]
