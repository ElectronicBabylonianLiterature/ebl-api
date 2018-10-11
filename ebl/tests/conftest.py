# pylint: disable=W0621
import datetime
import io
import json
from dictdiffer import diff
import pydash
import pytest
import mongomock
from falcon import testing
from falcon_auth import NoneAuthBackend

import ebl.app
from ebl.changelog import Changelog
from ebl.dictionary.dictionary import MongoDictionary
from ebl.fragmentarium.fragmentarium import Fragmentarium
from ebl.fragmentarium.fragment_repository import MongoFragmentRepository
from ebl.sign_list.sign_list import SignList
from ebl.sign_list.sign_repository import MongoSignRepository
from ebl.auth0 import Auth0User
from ebl.fragmentarium.fragment import Fragment


@pytest.fixture
def database():
    return mongomock.MongoClient().ebl


@pytest.fixture
def changelog(database):
    return Changelog(database)


@pytest.fixture
def dictionary(database):
    return MongoDictionary(database)


@pytest.fixture
def sign_repository(database):
    return MongoSignRepository(database)


@pytest.fixture
def sign_list(sign_repository):
    return SignList(sign_repository)


class TestFragmentRepository(MongoFragmentRepository):
    # Mongomock does not support $sample so we need to
    # stub methods using on it.
    def find_random(self):
        return [Fragment(self._mongo_collection.find_one({}))]

    def find_interesting(self):
        return [Fragment(self._mongo_collection.find_one({}))]


@pytest.fixture
def fragment_repository(database):
    return TestFragmentRepository(database)


@pytest.fixture
def fragmentarium(fragment_repository, changelog, sign_list):
    return Fragmentarium(fragment_repository, changelog, sign_list)


class FakeFile:
    # pylint: disable=R0903
    def __init__(self, filename, data, metadata):
        self.content_type = 'image/jpeg'
        self.filename = filename
        self.data = data
        self.length = len(data)
        self._file = io.BytesIO(data)
        self.metadata = metadata

    def read(self, size=-1):
        return self._file.read(size)


class TestFilesRepository:
    # pylint: disable=R0903
    # pylint: disable=R0201
    def __init__(self, *files):
        self._files = files

    def find(self, filename):

        try:
            return next(file
                        for file in self._files
                        if file.filename == filename)
        except StopIteration:
            raise KeyError


@pytest.fixture
def file():
    return FakeFile('folio1.jpg', b'oyoFLAbXbR', None)


@pytest.fixture
def file_with_allowed_scope():
    return FakeFile('folio2.jpg', b'ZTbvOTqvSW', {'scope': 'WGL-folios'})


@pytest.fixture
def file_with_restricted_scope():
    return FakeFile('folio3.jpg', b'klgsFPOutx', {'scope': 'restricted'})


@pytest.fixture
def file_repository(file, file_with_allowed_scope, file_with_restricted_scope):
    return TestFilesRepository(file,
                               file_with_allowed_scope,
                               file_with_restricted_scope)


@pytest.fixture
def user():
    return Auth0User(
        {
            'scope': [
                'read:words',
                'write:words',
                'transliterate:fragments',
                'read:fragments',
                'read:WGL-folios'
            ]
        },
        {
            'name': 'test.user@example.com',
            'https://ebabylon.org/eblName': 'User'
        }
    )


@pytest.fixture
def context(dictionary,
            sign_repository,
            file_repository,
            fragment_repository,
            changelog,
            user):
    # pylint: disable=R0913
    return {
        'auth_backend': NoneAuthBackend(lambda: user),
        'dictionary': dictionary,
        'sign_repository': sign_repository,
        'files': file_repository,
        'fragment_repository': fragment_repository,
        'changelog': changelog
    }


@pytest.fixture
def client(context):
    api = ebl.app.create_app(context)
    return testing.TestClient(api)


@pytest.fixture
def word():
    return {
        'lemma': ['part1', 'part2'],
        'homonym': 'I',
        'meaning': 'a meaning'
    }


@pytest.fixture
def fragment():
    return Fragment({
        '_id': '1',
        'cdliNumber': 'cdli-4',
        'bmIdNumber': 'bmId-2',
        'accession': 'accession-3',
        'transliteration': '',
        'notes': '',
        'folios': [
            {
                'name': 'WGL',
                'number': '1'
            },
            {
                'name': 'XXX',
                'number': '1'
            }
        ],
        'record': []
    })


@pytest.fixture
def another_fragment(fragment):
    return Fragment({
        **fragment.to_dict(),
        '_id': '2',
        'accession': 'accession-no-match',
        'cdliNumber': 'cdli-no-match',
        'notes': '',
        'folios': [
            {
                'name': 'WGL',
                'number': '2'
            },
            {
                'name': 'XXX',
                'number': '2'
            }
        ],
        'record': []
    })


@pytest.fixture
def transliterated_fragment():
    return Fragment({
        '_id': '3',
        'cdliNumber': 'cdli-5',
        'bmIdNumber': 'bmId-3',
        'accession': 'accession-4',
        'transliteration': (
            '1\'. [...-ku]-nu-ši [...]\n'
            '2\'. [...] GI₆ ana u₄-š[u ...]\n'
            '3\'. [... k]i-du u ba-ma-t[i ...]\n'
            '6\'. [...] x mu ta-ma-tu₂\n'
            '7\'. šu/|BI×IS|'
        ),
        'signs': (
            'KU NU IGI\n'
            'MI DIŠ UD ŠU\n'
            'KI DU U BA MA TI\n'
            'X MU TA MA UD\n'
            'ŠU/|BI×IS|'
        ),
        'notes': '',
        'folios': [
            {
                'name': 'WGL',
                'number': '3'
            },
            {
                'name': 'XXX',
                'number': '3'
            }
        ],
        'record': [{
            'user': 'Tester',
            'type': 'Transliteration',
            'date': datetime.datetime.utcnow().isoformat()
        }]
    })


@pytest.fixture
def make_changelog_entry(user):
    def _make_changelog_entry(resource_type, resource_id, old, new):
        return {
            'user_profile': pydash.map_keys(
                user.profile,
                lambda _, key: key.replace('.', '_')
            ),
            'resource_type': resource_type,
            'resource_id': resource_id,
            'date': datetime.datetime.utcnow().isoformat(),
            'diff':  json.loads(json.dumps(
                list(diff(old, new))
            ))
        }
    return _make_changelog_entry


@pytest.fixture
def signs():
    return [
        {
            '_id': sign_data[0],
            'lists': [],
            'unicode': [],
            'notes': [],
            'internalNotes': [],
            'literature': [],
            'values': [
                {
                    'value': value_data[0],
                    'subIndex': value_data[1],
                    'questionable': False,
                    'deprecated': False,
                    'notes': [],
                    'internalNotes': []
                }
                for value_data in sign_data[1]
            ],
            'forms': []
        }
        for sign_data in [
            ('KU', [('ku', 1)]),
            ('NU', [('nu', 1)]),
            ('IGI', [('ši', 1)]),
            ('DIŠ', [('ana', 1), ('1', 1)]),
            ('UD', [('u', 4), ('tu', 2)]),
            ('MI', [('mi', 1), ('gi', 6)]),
            ('KI', [('ki', 1)]),
            ('DU', [('du', 1)]),
            ('U', [('u', 1), ('10', 1)]),
            ('BA', [('ba', 1)]),
            ('MA', [('ma', 1)]),
            ('TI', [('ti', 1)]),
            ('MU', [('mu', 1)]),
            ('TA', [('ta', 1)]),
            ('ŠU', [('šu', 1)]),
            ('BU', [('gid', 2)])
        ]
    ]
