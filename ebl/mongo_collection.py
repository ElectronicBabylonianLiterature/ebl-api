from typing import Any, List, Mapping, Optional, Sequence, Union, cast
import inflect
from bson import ObjectId
from pymongo.client_session import ClientSession
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import AutoReconnect, DuplicateKeyError
from pymongo.results import UpdateResult
from ebl.errors import DuplicateError, NotFoundError


def singlar(noun: str) -> str:
    inflected = inflect.engine().singular_noun(noun)
    return noun if inflected is False else cast(str, inflected)


Session = Optional[ClientSession]
Document = Mapping[str, Any]
Update = Union[Mapping[str, Any], Sequence[Mapping[str, Any]]]


def retries_on_reconnect(session: Session) -> bool:
    return session is None or not session.in_transaction


class MongoCollection:
    def __init__(self, database: Database, collection: str):
        self.__database = database
        self.__collection = collection
        self.__resource_noun = singlar(collection)

    def insert_many(
        self, documents: Sequence[dict], ordered: bool = True, session: Session = None
    ) -> List[Any]:
        return (
            self.__get_collection()
            .insert_many(documents, ordered=ordered, session=session)
            .inserted_ids
        )

    def exists(self, query: Document, session: Session = None) -> bool:
        return bool(self.__get_collection().find_one(query, session=session))

    def insert_one(self, document: Document, session: Session = None) -> Any:
        try:
            return self.__insert_one(document, session)
        except DuplicateKeyError:
            raise DuplicateError(
                f"{self.__resource_noun} {document['_id']} already exists."
            )
        except AutoReconnect:
            if not retries_on_reconnect(session):
                raise
        try:
            return self.__insert_one(document, session)
        except DuplicateKeyError:
            return document["_id"]

    def find_one_by_id(self, id_: object, session: Session = None) -> Any:
        document = self.__get_collection().find_one({"_id": id_}, session=session)

        if document is None:
            raise self.__id_not_found_error(id_)
        else:
            return document

    def find_one(self, query, *args, **kwargs) -> Any:
        document = self.__get_collection().find_one(query, *args, **kwargs)

        if document is None:
            raise self.__not_found_error()
        else:
            return document

    def find_many(self, query, *args, **kwargs):
        return self.__get_collection().find(query, *args, **kwargs)

    def aggregate(self, pipeline, **kwargs):
        return self.__get_collection().aggregate(pipeline, **kwargs)

    def replace_one(
        self,
        document: Document,
        filter_: Optional[Document] = None,
        upsert: bool = False,
        session: Session = None,
    ) -> UpdateResult:
        result = self.__get_collection().replace_one(
            filter_ or {"_id": document["_id"]}, document, upsert, session=session
        )
        if result.matched_count == 0 and not upsert:
            raise self.__id_not_found_error(document["_id"])
        else:
            return result

    def delete_one(self, query: dict, session: Session = None) -> None:
        if not bool(query):
            raise ValueError("Empty Query for delete one not allowed")
        result = self.__get_collection().delete_one(query, session=session)
        if result.deleted_count == 0:
            raise self.__not_found_error()

    def delete_many(self, query: dict, session: Session = None) -> None:
        if not bool(query):
            raise ValueError("Empty Query for delete many not allowed")
        result = self.__get_collection().delete_many(query, session=session)
        if result.deleted_count == 0:
            raise self.__not_found_error()

    def update_one(
        self, query: Document, update: Update, session: Session = None
    ) -> UpdateResult:
        try:
            result = self.__update_one(query, update, session)
        except AutoReconnect:
            if not retries_on_reconnect(session):
                raise
            result = self.__update_one(query, update, session)
        if result.matched_count == 0:
            raise self.__not_found_error()
        return result

    def update_one_by_id(
        self, id_: object, update: Update, session: Session = None
    ) -> UpdateResult:
        try:
            return self.update_one({"_id": id_}, update, session)
        except NotFoundError as error:
            raise self.__id_not_found_error(id_) from error

    def update_many(self, query, update, **kwargs):
        return self.__get_collection().update_many(query, update, **kwargs)

    def count_documents(self, query: Document, session: Session = None) -> int:
        return self.__get_collection().count_documents(query, session=session)

    def create_index(self, index, **kwargs):
        return self.__get_collection().create_index(index, **kwargs)

    def index_information(self) -> Mapping:
        return self.__get_collection().index_information()

    def drop_index(self, index, **kwargs):
        return self.__get_collection().drop_index(index, **kwargs)

    def get_all_values(self, field: str, query: Optional[dict] = None) -> Sequence[str]:
        values = self.__get_collection().distinct(field, query or {})
        return [value for value in values if not isinstance(value, ObjectId)]

    def __insert_one(self, document: Document, session: Session) -> Any:
        return self.__get_collection().insert_one(document, session=session).inserted_id

    def __update_one(
        self, query: Document, update: Update, session: Session
    ) -> UpdateResult:
        return self.__get_collection().update_one(query, update, session=session)

    def __not_found_error(self) -> NotFoundError:
        return NotFoundError(f"{self.__resource_noun} not found.")

    def __id_not_found_error(self, id_: object) -> NotFoundError:
        return NotFoundError(f"{self.__resource_noun} {id_} not found.")

    def __get_collection(self) -> Collection:
        return self.__database[self.__collection]
