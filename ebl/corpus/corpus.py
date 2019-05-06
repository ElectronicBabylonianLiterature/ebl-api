from abc import ABC, abstractmethod

import pymongo

from ebl.corpus.text_hydrator import TextHydrator
from ebl.corpus.text_validator import TextValidator
from ebl.corpus.mongo_serializer import serialize, deserialize
from ebl.corpus.text import Text, TextId
from ebl.errors import NotFoundError
from ebl.mongo_repository import MongoRepository

COLLECTION = 'texts'


def text_not_found(id_: TextId) -> Exception:
    return NotFoundError(f'Text {id_.category}.{id_.index} not found.')


class TextRepository(ABC):
    @abstractmethod
    def create(self, text: Text) -> None:
        ...

    @abstractmethod
    def find(self, id_: TextId) -> Text:
        ...

    @abstractmethod
    def update(self, id_: TextId, text: Text) -> Text:
        ...


class MongoTextRepository(TextRepository):
    def __init__(self, database):
        self._mongo_repository = MongoRepository(database, COLLECTION)

    @property
    def _mongo_collection(self):
        return self._mongo_repository.get_collection()

    def create_indexes(self) -> None:
        self._mongo_collection.create_index([
            ('category', pymongo.ASCENDING),
            ('index', pymongo.ASCENDING)
        ], unique=True)

    def create(self, text: Text) -> None:
        self._mongo_repository.create(serialize(text))

    def find(self, id_: TextId) -> Text:
        mongo_text = self._find_one(id_)
        return deserialize(mongo_text)

    def update(self, id_: TextId, text: Text) -> Text:
        result = self._mongo_collection.update_one(
            {'category': id_.category, 'index': id_.index},
            {'$set': serialize(text)}
        )

        if result.matched_count == 0:
            raise text_not_found(id_)
        else:
            return self.find(text.id)

    def _find_one(self, id_: TextId) -> dict:
        mongo_text = self._mongo_collection.find_one({
            'category': id_.category,
            'index': id_.index
        })

        if mongo_text:
            return mongo_text
        else:
            raise text_not_found(id_)


class Corpus:
    def __init__(self,
                 repository: TextRepository,
                 bibliography,
                 changelog,
                 sign_list):
        self._repository: TextRepository = repository
        self._bibliography = bibliography
        self._changelog = changelog
        self._sign_list = sign_list

    def create(self, text: Text, user) -> None:
        self._validate_text(text)
        self._repository.create(text)
        new_dict: dict = {**serialize(text), '_id': text.id}
        self._changelog.create(
            COLLECTION,
            user.profile,
            {'_id': text.id},
            new_dict
        )

    def find(self, id_: TextId) -> Text:
        text = self._repository.find(id_)
        return self._hydrate_references(text)

    def update(self, id_: TextId, text: Text, user) -> Text:
        old_text = self._repository.find(id_)
        self._validate_text(text)
        old_dict: dict = {**serialize(old_text), '_id': old_text.id}
        new_dict: dict = {**serialize(text), '_id': text.id}
        self._changelog.create(
            COLLECTION,
            user.profile,
            old_dict,
            new_dict
        )
        updated_text = self._repository.update(id_, text)
        return self._hydrate_references(updated_text)

    def _validate_text(self, text: Text) -> None:
        text.accept(TextValidator(self._bibliography, self._sign_list))

    def _hydrate_references(self, text: Text) -> Text:
        hydrator = TextHydrator(self._bibliography)
        text.accept(hydrator)
        return hydrator.text
