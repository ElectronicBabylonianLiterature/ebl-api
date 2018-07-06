from ebl.mongo_repository import MongoRepository


class MongoFragmentarium(MongoRepository):

    def __init__(self, database):
        super().__init__(database, 'fragments')

    def update_transliteration(self, number, transliteration):
        self.get_collection().update_one(
            {'_id': number},
            {'$set': {'transliteration': transliteration}}
        )
