import attr
import pydash
import pymongo
from ebl.corpus.text import Text
from ebl.errors import NotFoundError, DataError
from ebl.mongo_repository import MongoRepository


COLLECTION = 'texts'


def validate(text):
    errors = []

    duplicate_sigla = (
        pydash
        .chain(text.chapters)
        .flat_map(lambda chapter: chapter.manuscripts)
        .map_(lambda manuscript: manuscript.siglum)
        .map_(lambda siglum, _, sigla: (siglum, sigla.count(siglum)))
        .filter(lambda entry: entry[1] > 1)
        .map_(lambda entry: entry[0])
        .uniq()
        .value()
    )
    if duplicate_sigla:
        errors.append(f'Duplicate sigla: {duplicate_sigla}.')

    double_numbered = (
        pydash
        .chain(text.chapters)
        .flat_map(lambda chapter: chapter.manuscripts)
        .filter(
            lambda manuscript:
            manuscript.museum_number and manuscript.accession
        )
        .map_(lambda manuscript: manuscript.siglum)
        .value()
    )
    if double_numbered:
        errors.append(
            f'Accession given when museum number present: {double_numbered}'
        )

    if errors:
        raise DataError(f'Bad text: {errors}.')


class MongoCorpus:

    def __init__(self, database, bibliography):
        self._mongo_repository = MongoRepository(database, COLLECTION)
        self._bibliography = bibliography

    def create_indexes(self):
        self._mongo_collection.create_index([
            ('category', pymongo.ASCENDING),
            ('index', pymongo.ASCENDING)
        ], unique=True)

    def create(self, text, _=None):
        validate(text)
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

    def update(self, category, index, text, _=None):
        validate(text)
        self._bibliography.validate_references(
            pydash
            .chain(text.chapters)
            .flat_map(lambda chapter: chapter.manuscripts)
            .flat_map(lambda manuscript: manuscript.references)
            .value()
        )
        result = self._mongo_collection.update_one(
            {'category': category, 'index': index},
            {'$set': text.to_dict()}
        )

        if result.matched_count == 0:
            raise NotFoundError(f'Text {category}.{index} not found.')
        else:
            return self.find(text.category, text.index)

    @property
    def _mongo_collection(self):
        return self._mongo_repository.get_collection()
