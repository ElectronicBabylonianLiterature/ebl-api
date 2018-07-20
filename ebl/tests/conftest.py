# pylint: disable=W0621
import pytest
import mongomock
from falcon import testing
from falcon_auth import NoneAuthBackend

import ebl.app

from ebl.dictionary.dictionary import MongoDictionary
from ebl.fragmentarium.fragmentarium import MongoFragmentarium


@pytest.fixture
def database():
    return mongomock.MongoClient().ebl


@pytest.fixture
def dictionary(database):
    return MongoDictionary(database)


@pytest.fixture
def fragmentarium(database):
    return MongoFragmentarium(database)


@pytest.fixture
def fetch_user_profile():
    def mock_fetch_user_profile(_):
        return {
            'name': 'test.user@example.com',
            'https://ebabylon.org/eblName': 'User'
        }

    return mock_fetch_user_profile


class TestFilesResource:
    # pylint: disable=R0903
    # pylint: disable=R0201
    def on_get(self, _req, resp, _file_name):
        resp.data = b'ZxYJy6Qj4s5fLErh'


@pytest.fixture
def client(dictionary, fragmentarium, fetch_user_profile):
    def user_loader():
        return {
            'scopes': []
        }

    auth_backend = NoneAuthBackend(user_loader)

    api = ebl.app.create_app(
        dictionary,
        fragmentarium,
        TestFilesResource(),
        auth_backend,
        fetch_user_profile
    )
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
        'transliteration': '',
        'notes': '',
        'record': []
    }
