from typing import Sequence


def join_reference_documents() -> Sequence[dict]:
    return [
        {"$unwind": {"path": "$references", "preserveNullAndEmptyArrays": True}},
        {
            "$lookup": {
                "from": "bibliography",
                "localField": "references.id",
                "foreignField": "_id",
                "as": "references.document",
            }
        },
        {
            "$set": {
                "references.document": {"$arrayElemAt": ["$references.document", 0]}
            }
        },
        {
            "$group": {
                "_id": "$_id",
                "references": {"$push": "$references"},
                "root": {"$first": "$$ROOT"},
            }
        },
        {
            "$replaceRoot": {
                "newRoot": {"$mergeObjects": ["$root", {"references": "$references"}]}
            }
        },
        {
            "$set": {
                "references": {
                    "$filter": {
                        "input": "$references",
                        "as": "reference",
                        "cond": {"$ne": ["$$reference", {}]},
                    }
                }
            }
        },
    ]
