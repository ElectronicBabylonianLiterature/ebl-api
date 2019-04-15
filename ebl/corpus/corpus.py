import attr
import pydash
import pymongo
from ebl.corpus.text import Text
from ebl.errors import NotFoundError, Defect
from ebl.mongo_repository import MongoRepository


COLLECTION = 'texts'


def raise_text_not_found(category, index):
    raise NotFoundError(f'Text {category}.{index} not found.')


def raise_invalid_reference(category, index, error):
    raise Defect(f'Text {category}.{index} has invalid manuscript'
                 f' references: "{error}"')


class MongoCorpus:

    def __init__(self, database, bibliography, changelog):
        self._mongo_repository = MongoRepository(database, COLLECTION)
        self._bibliography = bibliography
        self._changelog = changelog

    @property
    def _mongo_collection(self):
        return self._mongo_repository.get_collection()

    def create_indexes(self):
        self._mongo_collection.create_index([
            ('category', pymongo.ASCENDING),
            ('index', pymongo.ASCENDING)
        ], unique=True)

    def create(self, text, user):
        self._validate_references(text)
        object_id = self._mongo_repository.create(text.to_dict())
        self._changelog.create(
            COLLECTION,
            user.profile,
            {'_id': object_id},
            {**text.to_dict(), '_id': object_id}
        )
        return object_id

    def find(self, category, index):
        mongo_text = self._find_one(category, index)
        text = Text.from_dict(mongo_text)
        return self._hydrate_references(text)

    def update(self, category, index, text, user):
        self._validate_references(text)
        old_text = self._find_one(category, index)
        self._changelog.create(
            COLLECTION,
            user.profile,
            old_text,
            {**text.to_dict(), '_id': old_text['_id']}
        )
        result = self._mongo_collection.update_one(
            {'category': category, 'index': index},
            {'$set': text.to_dict()}
        )

        if result.matched_count == 0:
            raise_text_not_found(category, index)
        else:
            return self.find(text.category, text.index)

    def _find_one(self, category, index):
        mongo_text = self._mongo_collection.find_one({
            'category': category,
            'index': index
        })

        if mongo_text:
            return mongo_text
        else:
            raise_text_not_found(category, index)

    def _validate_references(self, text):
        self._bibliography.validate_references(
            pydash
            .chain(text.chapters)
            .flat_map(lambda chapter: chapter.manuscripts)
            .flat_map(lambda manuscript: manuscript.references)
            .value()
        )

    def _hydrate_references(self, text):
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
            raise_invalid_reference(text.category, text.index, error)