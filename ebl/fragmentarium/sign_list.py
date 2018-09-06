from ebl.mongo_repository import MongoRepository


COLLECTION = 'signs'


class SignList(MongoRepository):

    def __init__(self, database):
        super().__init__(database, COLLECTION)

    def search(self, reading, sub_index):
        sub_index_query =\
            {'$exists': False} if sub_index is None else sub_index
        return self.get_collection().find_one({
            'values': {
                '$elemMatch': {
                    'value': reading,
                    'subIndex': sub_index_query
                }
            }
        })
