# pylint: disable=W0621
import datetime
import io
import json
import attr
from dictdiffer import diff
import pydash
import pytest
import mongomock
from falcon import testing
from falcon_auth import NoneAuthBackend

import ebl.app
from ebl.changelog import Changelog
from ebl.dictionary.dictionary import MongoDictionary
from ebl.errors import NotFoundError
from ebl.fragmentarium.fragmentarium import Fragmentarium
from ebl.fragmentarium.fragment_repository import MongoFragmentRepository
from ebl.sign_list.sign_list import SignList
from ebl.sign_list.sign_repository import MongoSignRepository
from ebl.auth0 import Auth0User
from ebl.fragmentarium.fragment import (
    Fragment, Folios, Folio, Record, RecordEntry
)
from ebl.fragmentarium.lemmatization import Lemmatization


@pytest.fixture
def database():
    return mongomock.MongoClient().ebl


@pytest.fixture
def changelog(database):
    return Changelog(database)


class TestDictinary(MongoDictionary):
    # Mongomock does not support $addFields so we need to
    # stub the methods using them.
    def search_lemma(self, _):
        return [self.get_collection().find_one({})]


@pytest.fixture
def dictionary(database):
    return TestDictinary(database)


@pytest.fixture
def sign_repository(database):
    return MongoSignRepository(database)


@pytest.fixture
def sign_list(sign_repository):
    return SignList(sign_repository)


class TestFragmentRepository(MongoFragmentRepository):
    # Mongomock does not support $sample, or $concat so we need to
    # stub the methods using them.
    def find_random(self):
        return [Fragment.from_dict(self._mongo_collection.find_one({}))]

    def find_interesting(self):
        return [Fragment.from_dict(self._mongo_collection.find_one({}))]

    def folio_pager(self, _folio_name, _folio_number, _number):
        return {
            'previous': {
                'fragmentNumber': _number,
                'folioNumber': _folio_number
            },
            'next': {
                'fragmentNumber': _number,
                'folioNumber': _folio_number
            }
        }


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
            raise NotFoundError()


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
                'lemmatize:fragments',
                'read:fragments',
                'read:WGL-folios'
            ]
        },
        lambda: {
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
        "lemma": [
            'part1',
            'part2'
        ],
        "attested": True,
        "legacyLemma": "part1 part2",
        "homonym": "I",
        "_id": "part1 part2 I",
        "forms": [
            {
                "lemma": [
                    "form1"
                ],
                "notes": [],
                "attested": True
            },
            {
                "lemma": [
                    "form2", "part2"
                ],
                "notes": [
                    'a note'
                ],
                "attested": False
            },
        ],
        "meaning": "a meaning",
        "amplifiedMeanings": [
            {
                "meaning": "(*i/i*) meaning",
                "vowels": [
                    {
                        "value": [
                            "i",
                            "i"
                        ],
                        "notes": []
                    }
                ],
                "key": "G",
                "entries": []
            }
        ],
        "logograms": [],
        "derived": [
            [
                {
                    "lemma": [
                        "derived"
                    ],
                    "homonym": "I",
                    "notes": []
                }
            ]
        ],
        "derivedFrom": None,
        "source": "**part1 part2** source",
        "roots": [
            "wb'",
            "'b'"
        ],
        "pos": "V"
    }


@pytest.fixture
def fragment():
    return Fragment(
        number='1',
        cdli_number='cdli-4',
        bm_id_number='bmId-2',
        accession='accession-3',
        museum='Museum',
        collection='Collection',
        publication='publication',
        description='description',
        script='NA',
        folios=Folios((
            Folio('WGL', '1'),
            Folio('XXX', '1')
        ))
    )


@pytest.fixture
def another_fragment(fragment):
    return attr.evolve(
        fragment,
        number='2',
        accession='accession-no-match',
        cdli_number='cdli-no-match',
        bm_id_number='bmId-2',
        folios=Folios((
            Folio('WGL', '2'),
            Folio('XXX', '2')
        )),
        hits=5
    )


@pytest.fixture
def transliterated_fragment():
    return Fragment(
        number='3',
        cdli_number='cdli-5',
        bm_id_number='bmId-3',
        accession='accession-4',
        museum='Museum',
        collection='Collection',
        publication='publication',
        description='description',
        script='NA',
        lemmatization=Lemmatization([
            [
                {"value": "1'.", "uniqueLemma": []},
                {"value": "[...-ku]-nu-ši", "uniqueLemma": []},
                {"value": "[...]", "uniqueLemma": []}
            ],
            [
                {"value": "2'.", "uniqueLemma": []},
                {"value": "[...]", "uniqueLemma": []},
                {"value": "GI₆", "uniqueLemma": []},
                {"value": "ana", "uniqueLemma": []},
                {"value": "u₄-š[u", "uniqueLemma": []},
                {"value": "...]", "uniqueLemma": []}
            ],
            [
                {"value": "3'.", "uniqueLemma": []},
                {"value": "[...", "uniqueLemma": []},
                {"value": "k]i-du", "uniqueLemma": []},
                {"value": "u", "uniqueLemma": []},
                {"value": "ba-ma-t[i", "uniqueLemma": []},
                {"value": "...]", "uniqueLemma": []}
            ],
            [
                {"value": "6'.", "uniqueLemma": []},
                {"value": "[...]", "uniqueLemma": []},
                {"value": "x", "uniqueLemma": []},
                {"value": "mu", "uniqueLemma": []},
                {"value": "ta-ma-tu₂", "uniqueLemma": []}
            ],
            [
                {"value": "7'.", "uniqueLemma": []},
                {"value": "šu/|BI×IS|", "uniqueLemma": []}
            ]
        ]),
        signs=(
            'KU NU IGI\n'
            'MI DIŠ UD ŠU\n'
            'KI DU U BA MA TI\n'
            'X MU TA MA UD\n'
            'ŠU/|BI×IS|'
        ),
        folios=Folios((
            Folio('WGL', '3'),
            Folio('XXX', '3')
        )),
        record=Record((
            RecordEntry(
                'Tester',
                'Transliteration',
                datetime.datetime.utcnow().isoformat()
            ),
        ))
    )


@pytest.fixture
def lemmatized_fragment(transliterated_fragment):
    return attr.evolve(
        transliterated_fragment,
        number='4',
        lemmatization=Lemmatization([
            [
                {"value": "1'.", "uniqueLemma": []},
                {"value": "[...-ku]-nu-ši", "uniqueLemma": []},
                {"value": "[...]", "uniqueLemma": []}
            ],
            [
                {"value": "2'.", "uniqueLemma": []},
                {"value": "[...]", "uniqueLemma": []},
                {"value": "GI₆", "uniqueLemma": ["ginâ I"]},
                {"value": "ana", "uniqueLemma": ["ana I"]},
                {"value": "u₄-š[u", "uniqueLemma": ["ūsu I"]},
                {"value": "...]", "uniqueLemma": []}
            ],
            [
                {"value": "3'.", "uniqueLemma": []},
                {"value": "[...", "uniqueLemma": []},
                {"value": "k]i-du", "uniqueLemma": ["kīdu I"]},
                {"value": "u", "uniqueLemma": ["u I"]},
                {"value": "ba-ma-t[i", "uniqueLemma": ["bamātu I"]},
                {"value": "...]", "uniqueLemma": []}
            ],
            [
                {"value": "6'.", "uniqueLemma": []},
                {"value": "[...]", "uniqueLemma": []},
                {"value": "x", "uniqueLemma": []},
                {"value": "mu", "uniqueLemma": ["mu I"]},
                {"value": "ta-ma-tu₂", "uniqueLemma": ["tamalāku I"]}
            ],
            [
                {"value": "7'.", "uniqueLemma": []},
                {"value": "šu/|BI×IS|", "uniqueLemma": []}
            ]
        ])
    )


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
            'diff': json.loads(json.dumps(
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
