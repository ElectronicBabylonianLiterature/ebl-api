import pydash
from ebl.changelog import Changelog
from ebl.mongo_repository import MongoRepository


COLLECTION = 'bibliography'


def create_mongo_entry(entry):
    return pydash.map_keys(
        entry,
        lambda _, key: '_id' if key == 'id' else key
    )


def create_object_entry(entry):
    return pydash.map_keys(
        entry,
        lambda _, key: 'id' if key == '_id' else key
    )


class MongoBibliography():

    def __init__(self, database):
        self._mongo_repository = MongoRepository(database, COLLECTION)
        self._changelog = Changelog(database)

    def _get_collection(self):
        return self._mongo_repository.get_collection()

    def create(self, entry, user):
        mongo_entry = create_mongo_entry(entry)
        self._changelog.create(
            COLLECTION,
            user.profile,
            {'_id': entry['id']},
            mongo_entry
        )
        return self._mongo_repository.create(mongo_entry)

    def find(self, id_):
        data = self._mongo_repository.find(id_)
        return create_object_entry(data)

    def update(self, entry, user):
        old_entry = self._mongo_repository.find(entry['id'])
        mongo_entry = create_mongo_entry(entry)
        self._changelog.create(
            COLLECTION,
            user.profile,
            old_entry,
            mongo_entry
        )
        self._get_collection().replace_one(
            {'_id': entry['id']},
            mongo_entry
        )
