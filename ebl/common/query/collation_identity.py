def collation_safe_identity(value: str) -> dict:
    key = {
        "$replaceAll": {
            "input": {
                "$replaceAll": {
                    "input": {"$toString": value},
                    "find": "\\",
                    "replacement": "\\\\",
                }
            },
            "find": "\0",
            "replacement": "\\0",
        }
    }
    return {"$arrayToObject": [[{"k": key, "v": value}]]}


def original_identity_value(identity: str) -> dict:
    return {
        "$arrayElemAt": [
            {
                "$map": {
                    "input": {"$objectToArray": identity},
                    "as": "identity",
                    "in": "$$identity.v",
                }
            },
            0,
        ]
    }
