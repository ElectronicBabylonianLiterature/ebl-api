from bson.code import Code
from ebl.mongo_repository import MongoRepository


COLLECTION = 'fragments'
HAS_TRANSLITERATION = {'transliteration': {'$ne': ''}}
SAMPLE_SIZE_ONE = {
    '$sample': {
        'size': 1
    }
}


class MongoFragmentRepository(MongoRepository):
    def __init__(self, database):
        super().__init__(database, COLLECTION)

    def count_transliterated_fragments(self):
        return self.get_collection().count(HAS_TRANSLITERATION)

    def count_lines(self):
        count_lines = Code('function() {'
                           '  const lines = this.transliteration'
                           '    .split("\\n")'
                           '    .filter(line => /^\\d/.test(line));'
                           '  emit("lines", lines.length);'
                           '}')
        sum_lines = Code('function(key, values) {'
                         '  return values.reduce((acc, cur) => acc + cur, 0);'
                         '}')
        result = self.get_collection().inline_map_reduce(
            count_lines,
            sum_lines,
            query=HAS_TRANSLITERATION)

        return result[0]['value'] if result else 0

    def search(self, number):
        cursor = self.get_collection().find({
            '$or': [
                {'_id': number},
                {'cdliNumber': number},
                {'accession': number}
            ]
        })

        return [fragment for fragment in cursor]

    def find_random(self):
        cursor = self.get_collection().aggregate([
            {'$match': HAS_TRANSLITERATION},
            SAMPLE_SIZE_ONE
        ])

        return [fragment for fragment in cursor]

    def find_interesting(self):
        cursor = self.get_collection().aggregate([
            {
                '$match': {
                    '$and': [
                        {'transliteration': ''},
                        {'joins': []},
                        {'publication': ''},
                        {'hits': 0}
                    ]
                }
            },
            SAMPLE_SIZE_ONE
        ])

        return [fragment for fragment in cursor]

    def search_signs(self, query):
        cursor = self.get_collection().find({
            'signs': {'$regex': query}
        })
        return [fragment for fragment in cursor]

    def update_transliteration(self, number, updates, record):
        mongo_update = {
            '$set': updates
        }

        if record:
            mongo_update['$push'] = {'record': record}

        result = self.get_collection().update_one(
            {'_id': number},
            mongo_update
        )

        if result.matched_count == 0:
            raise KeyError
