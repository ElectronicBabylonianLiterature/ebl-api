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
from ebl.fragmentarium.fragmentarium import MongoFragmentarium
from ebl.fragmentarium.sign_list import MongoSignList


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
def fragmentarium(database):
    return MongoFragmentarium(database)


@pytest.fixture
def sign_list(database):
    return MongoSignList(database)


@pytest.fixture
def user_profile():
    return {
        'name': 'test.user@example.com',
        'https://ebabylon.org/eblName': 'User'
    }


@pytest.fixture
def fetch_user_profile(user_profile):
    def mock_fetch_user_profile(_):
        return user_profile

    return mock_fetch_user_profile


class FakeFile:
    # pylint: disable=R0903
    def __init__(self, filename, data):
        self.content_type = 'image/jpeg'
        self.filename = filename
        self.data = data
        self.length = len(data)
        self._file = io.BytesIO(data)

    def read(self, size=-1):
        return self._file.read(size)


class TestFilesRepository:
    # pylint: disable=R0903
    # pylint: disable=R0201
    def __init__(self, file):
        self._file = file

    def find(self, filename):
        if self._file.filename == filename:
            return self._file
        else:
            raise KeyError


@pytest.fixture
def file():
    return FakeFile('folio.jpg', b'ZxYJy6Qj4s5fLErh')


@pytest.fixture
def file_repository(file):
    return TestFilesRepository(file)


@pytest.fixture
def context(dictionary,
            fragmentarium,
            sign_list,
            fetch_user_profile,
            file_repository):
    def user_loader():
        return {
            'scope': [
                'read:words',
                'write:words',
                'transliterate:fragments',
                'read:fragments'
            ]
        }

    return {
        'auth_backend': NoneAuthBackend(user_loader),
        'dictionary': dictionary,
        'fragmenatrium': fragmentarium,
        'sign_list': sign_list,
        'files': file_repository,
        'fetch_user_profile': fetch_user_profile
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
    return {
        '_id': '1',
        'cdliNumber': 'cdli-4',
        'bmIdNumber': 'bmId-2',
        'accession': 'accession-3',
        'transliteration': '',
        'notes': '',
        'record': []
    }


@pytest.fixture
def transliterated_fragment():
    return {
        '_id': '3',
        'cdliNumber': 'cdli-5',
        'bmIdNumber': 'bmId-3',
        'accession': 'accession-4',
        'transliteration': (
            '1\'. [...-ku]-nu-ši [...]\n'
            '2\'. [...] GI₆ ana u₄-m[i ...]\n'
            '3\'. [... k]i-du u ba-ma-t[i ...]\n'
            '6\'. [...] x mu ta-ma-tu₂\n'
        ),
        'signs': (
            'KU NU IGI\n'
            'GI₆ DIŠ UD MI\n'
            'KI DU U BA MA TI\n'
            'X MU TA MA UD'
        ),
        'notes': '',
        'record': []
    }


@pytest.fixture
def make_changelog_entry(user_profile):
    def _make_changelog_entry(resource_type, resource_id, old, new):
        return {
            'user_profile': pydash.map_keys(
                user_profile,
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
