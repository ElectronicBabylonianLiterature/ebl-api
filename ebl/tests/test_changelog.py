import datetime
import json
from dictdiffer import diff
from freezegun import freeze_time
import mongomock

from ebl.changelog import Changelog

COLLECTION = 'changelog'
USER = 'user'
RESOURCE_TYPE = 'type'
RESOURCE_ID = 'id'
OLD = {
    '_id': RESOURCE_ID,
    'a': 'foo',
    'b': 'bar'
}
NEW = {
    '_id': RESOURCE_ID,
    'b': 'baz',
    'c': 43
}


@freeze_time("2018-09-07 15:41:24.032")
def test_add_transliteration():
    database = mongomock.MongoClient().ebl
    changelog = Changelog(database)

    _id = changelog.create(RESOURCE_TYPE, USER, OLD, NEW)

    expected_diff = json.loads(json.dumps(list(diff(OLD, NEW))))
    expected = {
        '_id': _id,
        'user': USER,
        'resource_type': RESOURCE_TYPE,
        'resource_id': RESOURCE_ID,
        'date': datetime.datetime.utcnow().isoformat(),
        'diff': expected_diff
    }
    assert database[COLLECTION].find_one({'_id': _id}) == expected
