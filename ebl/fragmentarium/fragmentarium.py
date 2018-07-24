import datetime
from bson.code import Code
from ebl.mongo_repository import MongoRepository

TRANSLITERATION = 'Transliteration'
REVISION = 'Revision'
HAS_TRANSLITERATION = {'transliteration': {'$ne': ''}}


class MongoFragmentarium(MongoRepository):

    def __init__(self, database):
        super().__init__(database, 'fragments')

    def update_transliteration(self, number, updates, user):
        fragment = self.get_collection().find_one(
            {'_id': number},
            {'transliteration': 1}
        )

        if fragment:
            self._update(updates, fragment, user)
        else:
            raise KeyError

    def _update(self, updates, fragment, user):
        mongo_update = {
            '$set': {
                'transliteration': updates['transliteration'],
                'notes': updates['notes']
            }
        }

        old_transliteration = fragment['transliteration']
        if updates['transliteration'] != old_transliteration:
            record_type = REVISION if old_transliteration else TRANSLITERATION
            mongo_update['$push'] = {'record': {
                'user': user,
                'type': record_type,
                'date': datetime.datetime.utcnow().isoformat()
            }}

        self.get_collection().update_one(
            {'_id': fragment['_id']},
            mongo_update
        )

    def statistics(self):
        return {
            'transliteratedFragments': self._get_transliterated_fragments(),
            'lines': self._get_lines()
        }

    def _get_transliterated_fragments(self):
        return self.get_collection().count(HAS_TRANSLITERATION)

    def _get_lines(self):
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

        return [word for word in cursor]
