import datetime
from bson.code import Code
import pydash
from ebl.changelog import Changelog
from ebl.mongo_repository import MongoRepository

COLLECTION = 'fragments'
EBL_NAME = 'https://ebabylon.org/eblName'
TRANSLITERATION = 'Transliteration'
REVISION = 'Revision'
HAS_TRANSLITERATION = {'transliteration': {'$ne': ''}}
SAMPLE_SIZE_ONE = {
    '$sample': {
        'size': 1
    }
}


def _create_record(old_transliteration, user_profile):
    record_type = REVISION if old_transliteration else TRANSLITERATION
    user = user_profile[EBL_NAME] or user_profile['name']
    return {
        'user': user,
        'type': record_type,
        'date': datetime.datetime.utcnow().isoformat()
    }


class MongoFragmentarium(MongoRepository):

    def __init__(self, database):
        super().__init__(database, COLLECTION)
        self._changelog = Changelog(database)

    def update_transliteration(self, number, updates, user_profile):
        fragment = self.get_collection().find_one(
            {'_id': number},
            {
                'transliteration': 1,
                'notes': 1
            }
        )

        if fragment:
            self._update(updates, fragment, user_profile)
        else:
            raise KeyError

    def _update(self, updates, fragment, user_profile):
        updated_fragment = {
            'transliteration': updates['transliteration'],
            'notes': updates['notes']
        }
        mongo_update = {
            '$set': updated_fragment
        }

        old_transliteration = fragment['transliteration']
        if updates['transliteration'] != old_transliteration:
            record = _create_record(old_transliteration, user_profile)
            mongo_update['$push'] = {
                'record': record
            }

        self._changelog.create(
            COLLECTION,
            user_profile,
            fragment,
            pydash.defaults(updated_fragment,
                            {'_id': fragment['_id']})
        )
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

    def search_signs(self, signs):
        sign_separator = ' '
        line_regexps = [
            fr'(?<![^ |\n]){sign_separator.join(row)}'
            for row in signs
        ]
        lines_regexp = r'( .*)?\n.*'.join(line_regexps)
        query = fr'{lines_regexp}(?![^ |\n])'

        cursor = self.get_collection().find(
            {'signs': {
                '$regex': query
            }}
        )

        return [fragment for fragment in cursor]
