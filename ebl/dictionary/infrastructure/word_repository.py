from typing import Sequence, Optional

from ebl.changelog import Changelog
from ebl.dictionary.application.word_repository import WordRepository
from ebl.dictionary.domain.word import WordId
from ebl.mongo_collection import MongoCollection
from ebl.dictionary.domain.dictionary_query import DictionaryFieldQuery

COLLECTION = "words"
LEMMA_SEARCH_LIMIT = 15


def _create_substring_expression(query, _input):
    return {
        "$eq": [
            {
                "$substrCP": [
                    {
                        "$reduce": {
                            "input": _input,
                            "initialValue": "",
                            "in": {"$concat": ["$$value", "$$this", " "]},
                        }
                    },
                    0,
                    len(query),
                ]
            },
            query,
        ]
    }


def _create_lemma_search_pipeline(query):
    return [
        {
            "$match": {
                "$or": [
                    {"$expr": _create_substring_expression(query, "$lemma")},
                    {
                        "$expr": {
                            "$anyElementTrue": {
                                "$map": {
                                    "input": "$forms",
                                    "as": "form",
                                    "in": _create_substring_expression(
                                        query, "$$form.lemma"
                                    ),
                                }
                            }
                        }
                    },
                ]
            }
        },
        {
            "$addFields": {
                "lemmaLength": {
                    "$sum": {
                        "$map": {
                            "input": "$lemma",
                            "as": "part",
                            "in": {"$strLenCP": "$$part"},
                        }
                    }
                }
            }
        },
        {"$sort": {"lemmaLength": 1, "_id": 1}},
        {"$limit": LEMMA_SEARCH_LIMIT},
        {"$project": {"lemmaLength": 0}},
    ]


def _create_query_by_lemma(word: str, collate: bool) -> dict:
    regex_options = "i" if collate else ""
    return {
        "$or": [
            {"lemma": {"$regex": rf"^{word}", "$options": regex_options}},
            {"forms.lemma": {"$regex": rf"^{word}", "$options": regex_options}},
        ]
    }


def _create_query_by_meaning(meaning: str, collate: bool) -> dict:
    regex_options = "i" if collate else ""
    return {
        "$or": [
            {"meaning": {"$regex": meaning, "$options": regex_options}},
            {
                "amplifiedMeanings.meaning": {
                    "$regex": meaning,
                    "$options": regex_options,
                }
            },
            {
                "amplifiedMeanings.entries.meaning": {
                    "$regex": meaning,
                    "$options": regex_options,
                }
            },
        ]
    }


def _create_query_by_root(root: str, collate: bool) -> dict:
    regex_options = "i" if collate else ""
    return {"roots": {"$regex": rf"^{root}$", "$options": regex_options}}


def _create_query_by_vowel_class(vowel_class: str) -> dict:
    return {
        "$or": [
            {"amplifiedMeanings.vowels.value": vowel_class.split("/")},
            {"amplifiedMeanings.entries.vowels.value": vowel_class.split("/")},
        ]
    }


class MongoWordRepository(WordRepository):
    def __init__(self, database):
        self._collection = MongoCollection(database, COLLECTION)
        self._changelog = Changelog(database)

    def create(self, document):
        return self._collection.insert_one(document)

    def query_by_id(self, id_: WordId):
        return self._collection.find_one_by_id(id_)

    def query_by_ids(self, ids: Sequence[str]) -> Sequence:
        cursor = self._collection.aggregate(
            [
                {
                    "$match": {"_id": {"$in": ids}},
                }
            ]
        )
        return list(cursor)

    def query_by_lemma_meaning_root_vowels(
        self,
        word: Optional[DictionaryFieldQuery] = None,
        meaning: Optional[DictionaryFieldQuery] = None,
        root: Optional[DictionaryFieldQuery] = None,
        vowel_class: Optional[DictionaryFieldQuery] = None,
    ) -> Sequence:
        cursor = self._collection.aggregate(
            [
                {
                    "$match": {
                        "$and": [
                            _create_query_by_lemma(word.value, word.use_collations)
                            if word
                            else {},
                            _create_query_by_meaning(
                                meaning.value, meaning.use_collations
                            )
                            if meaning
                            else {},
                            _create_query_by_root(root.value, root.use_collations)
                            if root
                            else {},
                            _create_query_by_vowel_class(vowel_class.value)
                            if vowel_class
                            else {},
                        ]
                    },
                }
            ],
        )
        return list(cursor)

    def query_by_lemma_prefix(self, query: str) -> Sequence:
        cursor = self._collection.aggregate(
            _create_lemma_search_pipeline(query),
            collation={"locale": "en", "strength": 1, "normalization": True},
        )

        return list(cursor)

    def list_all_words(self) -> None:
        return list(id for id in self._collection.get_all_values("_id"))

    def update(self, word) -> None:
        self._collection.update_one({"_id": word["_id"]}, {"$set": word})
