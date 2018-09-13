from ebl.mongo_repository import MongoRepository
from ebl.fragmentarium.clean_transliteration import clean_transliteration
from ebl.fragmentarium.transliteration_to_signs import transliteration_to_signs

COLLECTION = 'signs'


class MongoSignList(MongoRepository):

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


    def map_transliteration(self, transliteration):
        cleaned_transliteration = clean_transliteration(transliteration)
        return transliteration_to_signs(cleaned_transliteration, self)
