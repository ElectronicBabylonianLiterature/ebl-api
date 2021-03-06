from typing import Any

import inflect  # pyre-ignore[21]
from pymongo.collection import Collection  # pyre-ignore[21]
from pymongo.database import Database  # pyre-ignore[21]
from pymongo.errors import DuplicateKeyError  # pyre-ignore[21]

from ebl.errors import DuplicateError, NotFoundError


class MongoCollection:
    def __init__(self, database: Database, collection: str):  # pyre-ignore[11]
        self.__database = database
        self.__collection = collection
        self.__resource_noun = (
            inflect.engine().singular_noun(collection) or collection
        ).title()

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

    def __get_collection(self) -> Collection:  # pyre-ignore[11]
        return self.__database[self.__collection]
