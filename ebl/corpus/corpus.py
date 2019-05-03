from abc import ABC, abstractmethod

import attr
import pydash
import pymongo

from ebl.corpus.text import Text, TextId, Chapter
from ebl.errors import Defect, NotFoundError, DataError
from ebl.mongo_repository import MongoRepository
from ebl.fragment.transliteration import Transliteration, TransliterationError
from ebl.fragmentarium.validator import Validator
from text.labels import LineNumberLabel

COLLECTION = 'texts'


def text_not_found(id_: TextId) -> Exception:
    return NotFoundError(f'Text {id_.category}.{id_.index} not found.')


def invalid_atf(chapter: Chapter,
                line_number: LineNumberLabel,
                manuscript_id: int) -> Exception:
    siglum = [manuscript.siglum
              for manuscript in chapter.manuscripts
              if manuscript.id == manuscript_id][0]
    return DataError(
        f'Invalid transliteration on'
        f' line {line_number.to_value()}'
        f' manuscript {siglum}.'
    )


def invalid_reference(id_: TextId, error: Exception) -> Exception:
    return Defect(f'Text {id_.category}.{id_.index} has invalid manuscript'
                  f' references: "{error}"')


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
        self._mongo_repository.create(text.to_dict())

    def find(self, id_: TextId) -> Text:
        mongo_text = self._find_one(id_)
        return Text.from_dict(mongo_text)

    def update(self, id_: TextId, text: Text) -> Text:
        result = self._mongo_collection.update_one(
            {'category': id_.category, 'index': id_.index},
            {'$set': text.to_dict()}
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
        self.validate_text(text)
        self._repository.create(text)
        new_dict: dict = {**text.to_dict(), '_id': text.id}
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
        self.validate_text(text)
        old_dict: dict = {**old_text.to_dict(), '_id': old_text.id}
        new_dict: dict = {**text.to_dict(), '_id': text.id}
        self._changelog.create(
            COLLECTION,
            user.profile,
            old_dict,
            new_dict
        )
        updated_text = self._repository.update(id_, text)
        return self._hydrate_references(updated_text)

    def validate_text(self, text: Text) -> None:
        self._validate_atf(text)
        self._validate_references(text)

    def _validate_atf(self, text: Text) -> None:
        for chapter in text.chapters:
            for line in chapter.lines:
                for manuscript in line.manuscripts:
                    try:
                        Validator(Transliteration(manuscript.line.atf)
                                  .with_signs(self._sign_list)).validate()
                    except TransliterationError:
                        raise invalid_atf(chapter,
                                          line.number,
                                          manuscript.manuscript_id)

    def _validate_references(self, text: Text) -> None:
        self._bibliography.validate_references(
            pydash
            .chain(text.chapters)
            .flat_map(lambda chapter: chapter.manuscripts)
            .flat_map(lambda manuscript: manuscript.references)
            .value()
        )

    def _hydrate_references(self, text: Text) -> Text:
        try:
            return attr.evolve(text, chapters=tuple(
                attr.evolve(chapter, manuscripts=tuple(
                    attr.evolve(manuscript, references=tuple(
                        attr.evolve(
                            reference,
                            document=self._bibliography.find(reference.id)
                        )
                        for reference in manuscript.references
                    ))
                    for manuscript in chapter.manuscripts
                ))
                for chapter in text.chapters
            ))
        except NotFoundError as error:
            raise invalid_reference(text.id, error)
