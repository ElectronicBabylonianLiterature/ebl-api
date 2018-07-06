from ebl.mongo_repository import MongoRepository


class MongoFragmentarium(MongoRepository):

    def __init__(self, database):
        super().__init__(database, 'fragments')
