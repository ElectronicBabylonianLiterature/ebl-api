import inflect
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from ebl.errors import DuplicateError, NotFoundError


class MongoRepository:

    def __init__(self, database: Database, collection: str):
        self.__database = database
        self.__collection = collection
        self.__resource_noun = (inflect.engine().singular_noun(collection) or
                                collection).title()

    def _insert_one(self, document):
        try:
            return self.__get_collection().insert_one(document).inserted_id
        except DuplicateKeyError:
            raise DuplicateError(
                f'{self.__resource_noun} {document["_id"]} already exists.'
            )

    def _find_one_by_id(self, id_):
        return self._find_one({'_id': id_})

    def _find_one(self, query):
        document = self.__get_collection().find_one(query)

        if document is None:
            raise self.__not_found_error(query)
        else:
            return document

    def _find_many(self, query):
        return self.__get_collection().find(query)

    def _aggregate(self, pipeline, **kwargs):
        return self.__get_collection().aggregate(pipeline, **kwargs)

    def _replace_one(self, document):
        result = self.__get_collection().replace_one(
            {'_id': document['_id']},
            document
        )
        if result.matched_count == 0:
            raise self.__not_found_error(document['_id'])
        else:
            return result

    def _update_one(self, query, update):
        result = self.__get_collection().update_one(query, update)
        if result.matched_count == 0:
            raise self.__not_found_error(query)
        else:
            return result

    def _count_documents(self, query) -> int:
        return self.__get_collection().count_documents(query)

    def _create_index(self, index, **kwargs):
        return self.__get_collection().create_index(index, **kwargs)

    def __not_found_error(self, query):
        return NotFoundError(
            f'{self.__resource_noun} {query} not found.'
        )

    def __get_collection(self) -> Collection:
        return self.__database[self.__collection]
