from ebl.errors import NotFoundError


class MongoRepository:

    def __init__(self, database, collection):
        self._database = database
        self.collection = collection

    def get_collection(self):
        return self._database[self.collection]

    def create(self, document):
        return self.get_collection().insert_one(document).inserted_id

    def find(self, object_id):
        document = self.get_collection().find_one({'_id': object_id})

        if document is None:
            raise NotFoundError(f'Resource {object_id} not found.')
        else:
            return document
