import attr
import pydash
import pymongo
from ebl.corpus.text import Text
from ebl.errors import NotFoundError, DataError
from ebl.mongo_repository import MongoRepository


COLLECTION = 'texts'


class MongoCorpus:

    def __init__(self, database, bibliography, changelog):
        self._mongo_repository = MongoRepository(database, COLLECTION)
        self._bibliography = bibliography
        self._changelog = changelog

    def create_indexes(self):
        self._mongo_collection.create_index([
            ('category', pymongo.ASCENDING),
            ('index', pymongo.ASCENDING)
        ], unique=True)

    def create(self, text, _=None):
        self._bibliography.validate_references(
            pydash
            .chain(text.chapters)
            .flat_map(lambda chapter: chapter.manuscripts)
            .flat_map(lambda manuscript: manuscript.references)
            .value()
        )
        return self._mongo_repository.create(text.to_dict())

    def find(self, category, index):
        mongo_text = self._mongo_collection.find_one({
            'category': category,
            'index': index
        })

        if mongo_text:
            text = Text.from_dict(mongo_text)
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
                raise Exception(error)
        else:
            raise NotFoundError(f'Text {category}.{index} not found.')

    def update(self, category, index, text, user):
        self._bibliography.validate_references(
            pydash
            .chain(text.chapters)
            .flat_map(lambda chapter: chapter.manuscripts)
            .flat_map(lambda manuscript: manuscript.references)
            .value()
        )
        old_text = self._mongo_collection.find_one({
            'category': category,
            'index': index
        })
        if old_text:
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
                raise NotFoundError(f'Text {category}.{index} not found.')
            else:
                return self.find(text.category, text.index)
        else:
            raise NotFoundError(f'Text {category}.{index} not found.')

    @property
    def _mongo_collection(self):
        return self._mongo_repository.get_collection()
