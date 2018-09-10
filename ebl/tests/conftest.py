# pylint: disable=W0621
import datetime
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


class TestFilesResource:
    # pylint: disable=R0903
    # pylint: disable=R0201
    def on_get(self, _req, resp, _file_name):
        resp.data = b'ZxYJy6Qj4s5fLErh'


@pytest.fixture
def client(dictionary, fragmentarium, fetch_user_profile):
    def user_loader():
        return {
            'scope': [
                'read:words',
                'write:words',
                'transliterate:fragments',
                'read:fragments'
            ]
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
        'cdliNumber': 'cdli-4',
        'bmIdNumber': 'bmId-2',
        'accession': 'accession-3',
        'transliteration': '',
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
