from typing import Any, cast

import inflect
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from ebl.errors import DuplicateError, NotFoundError


def singlar(noun: str) -> str:
    inflected = inflect.engine().singular_noun(noun)
    return noun if inflected is False else cast(str, inflected)


class MongoCollection:
    def __init__(self, database: Database, collection: str):
        self.__database = database
        self.__collection = collection
        self.__resource_noun = singlar(collection)

    def insert_one(self, document):
        try:
            return self.__get_collection().insert_one(document).inserted_id
        except DuplicateKeyError:
            raise DuplicateError(
                f'{self.__resource_noun} {document["_id"]} already exists.'
            )

    def find_one_by_id(self, id_):
        return self.find_one({"_id": id_})

    def find_one(self, query, *args, **kwargs) -> Any:
        document = self.__get_collection().find_one(query, *args, **kwargs)

        if document is None:
            raise self.__not_found_error(query)
        else:
            return document

    def find_many(self, query, *args, **kwargs):
        return self.__get_collection().find(query, *args, **kwargs)

    def aggregate(self, pipeline, **kwargs):
        return self.__get_collection().aggregate(pipeline, **kwargs)

    def replace_one(self, document, filter_=None, upsert=False):
        result = self.__get_collection().replace_one(
            filter_ or {"_id": document["_id"]}, document, upsert
        )
        if result.matched_count == 0 and not upsert:
            raise self.__not_found_error(document["_id"])
        else:
            return result

    def update_one(self, query, update):
        result = self.__get_collection().update_one(query, update)
        if result.matched_count == 0:
            raise self.__not_found_error(query)
        else:
            return result

    def count_documents(self, query) -> int:
        return self.__get_collection().count_documents(query)

    def create_index(self, index, **kwargs):
        return self.__get_collection().create_index(index, **kwargs)

    def __not_found_error(self, query):
        return NotFoundError(f"{self.__resource_noun} {query} not found.")

    def __get_collection(self) -> Collection:
        return self.__database[self.__collection]
