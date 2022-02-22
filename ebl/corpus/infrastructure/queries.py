from typing import List

from ebl.corpus.domain.chapter import ChapterId
from ebl.corpus.infrastructure.collections import CHAPTERS_COLLECTION
from ebl.fragmentarium.infrastructure.queries import is_in_fragmentarium
from ebl.transliteration.domain.translation_line import DEFAULT_LANGUAGE


def chapter_id_query(id_: ChapterId) -> dict:
    return {
        "textId.genre": id_.text_id.genre.value,
        "textId.category": id_.text_id.category,
        "textId.index": id_.text_id.index,
        "stage": id_.stage.value,
        "name": id_.name,
    }


def join_uncertain_fragments() -> List[dict]:
    return [
        {
            "$unwind": {
                "path": "$uncertainFragments",
                "preserveNullAndEmptyArrays": True,
            }
        },
        *is_in_fragmentarium("uncertainFragments", "isInFragmentarium"),
        {
            "$group": {
                "_id": "$_id",
                "uncertainFragments": {
                    "$push": {
                        "museumNumber": "$uncertainFragments",
                        "isInFragmentarium": "$isInFragmentarium",
                    }
                },
                "root": {"$first": "$$ROOT"},
            }
        },
        {
            "$replaceRoot": {
                "newRoot": {
                    "$mergeObjects": [
                        "$root",
                        {"uncertainFragments": "$uncertainFragments"},
                    ]
                }
            }
        },
        {
            "$set": {
                "uncertainFragments": {
                    "$filter": {
                        "input": "$uncertainFragments",
                        "as": "uncertainFragment",
                        "cond": {
                            "$ne": [
                                {"$type": "$$uncertainFragment.museumNumber"},
                                "missing",
                            ]
                        },
                    }
                }
            }
        },
        {"$project": {"isInFragmentarium": 0}},
    ]


def join_chapters(include_uncertain_fragmnets: bool) -> List[dict]:
    return [
        {
            "$lookup": {
                "from": CHAPTERS_COLLECTION,
                "let": {"genre": "$genre", "category": "$category", "index": "$index"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$textId.genre", "$$genre"]},
                                    {"$eq": ["$textId.category", "$$category"]},
                                    {"$eq": ["$textId.index", "$$index"]},
                                ]
                            }
                        }
                    },
                    {"$addFields": {"firstLine": {"$first": "$lines"}}},
                    {
                        "$project": {
                            "stage": 1,
                            "name": 1,
                            "order": 1,
                            "translation": "$firstLine.translation",
                            "uncertainFragments": 1,
                        }
                    },
                    *(
                        join_uncertain_fragments()
                        if include_uncertain_fragmnets
                        else [{"$project": {"uncertainFragments": 0}}]
                    ),
                    {"$sort": {"order": 1}},
                    {"$project": {"_id": 0, "order": 0}},
                ],
                "as": "chapters",
            }
        },
        {"$project": {"_id": 0}},
    ]


def aggregate_chapter_display(id_: ChapterId) -> List[dict]:
    return [
        {"$match": chapter_id_query(id_)},
        {
            "$addFields": {
                "id": {"textId": "$textId", "stage": "$stage", "name": "$name"},
                "lines": {
                    "$map": {
                        "input": "$lines",
                        "as": "line",
                        "in": {
                            "number": "$$line.number",
                            "isSecondLineOfParallelism": "$$line.isSecondLineOfParallelism",
                            "isBeginningOfSection": "$$line.isBeginningOfSection",
                            "translation": {
                                "$arrayElemAt": [
                                    {
                                        "$map": {
                                            "input": {
                                                "$filter": {
                                                    "input": "$$line.translation",
                                                    "as": "translation",
                                                    "cond": {
                                                        "eq": [
                                                            "$$translation.language",
                                                            DEFAULT_LANGUAGE,
                                                        ]
                                                    },
                                                }
                                            },
                                            "as": "en_translation",
                                            "in": "$$en_translation.parts",
                                        }
                                    },
                                    0,
                                ]
                            },
                            "intertext": {
                                "$arrayElemAt": [
                                    {
                                        "$map": {
                                            "input": "$$line.variants",
                                            "as": "variant",
                                            "in": "$$variant.intertext",
                                        }
                                    },
                                    0,
                                ]
                            },
                            "reconstruction": {
                                "$arrayElemAt": [
                                    {
                                        "$map": {
                                            "input": "$$line.variants",
                                            "as": "variant",
                                            "in": "$$variant.reconstruction",
                                        }
                                    },
                                    0,
                                ]
                            },
                        },
                    }
                },
            }
        },
        {
            "$project": {
                "_id": False,
                "id": True,
                "lines": True,
                "authors": True,
                "translators": True,
            }
        },
    ]
