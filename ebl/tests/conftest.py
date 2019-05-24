import datetime
import io
import json

import attr
import mongomock
import pydash
import pytest
from dictdiffer import diff
from falcon import testing
from falcon_auth import NoneAuthBackend

import ebl.app
import ebl.fragment.fragment_factory as fragment_factory_
from ebl.auth0 import Auth0User
from ebl.bibliography.bibliography import (
    MongoBibliography, create_object_entry
)
from ebl.changelog import Changelog
from ebl.corpus.corpus import Corpus
from ebl.corpus.mongo_text_repository import MongoTextRepository
from ebl.dictionary.dictionary import MongoDictionary
from ebl.errors import NotFoundError
from ebl.fragmentarium.fragment_repository import MongoFragmentRepository
from ebl.fragmentarium.fragmentarium import Fragmentarium
from ebl.sign_list.sign_list import SignList
from ebl.sign_list.sign_repository import MongoSignRepository
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.text.line import TextLine
from ebl.text.text import Text
from ebl.text.token import Token, Word
from ebl.dictionary.word import UniqueLemma


@pytest.fixture
def database():
    return mongomock.MongoClient().ebl


@pytest.fixture
def changelog(database):
    return Changelog(database)


class TestDictionary(MongoDictionary):
    # Mongomock does not support $addFields so we need to
    # stub the methods using them.
    def search_lemma(self, _):
        return [self.get_collection().find_one({})]


@pytest.fixture
def dictionary(database):
    return TestDictionary(database)


class TestBibliography(MongoBibliography):
    # Mongomock does not support $addFields so we need to
    # stub the methods using them.
    def search(self, _author=None, _year=None, _title=None):
        return [create_object_entry(
            self._mongo_repository.get_collection().find_one({})
        )]


@pytest.fixture
def bibliography(database):
    return TestBibliography(database)


@pytest.fixture
def sign_repository(database):
    return MongoSignRepository(database)


@pytest.fixture
def sign_list(sign_repository):
    return SignList(sign_repository)


@pytest.fixture
def text_repository(database):
    return MongoTextRepository(database,)


@pytest.fixture
def corpus(text_repository, bibliography, changelog, sign_list):
    return Corpus(text_repository, bibliography, changelog, sign_list)


class TestFragmentRepository(MongoFragmentRepository):
    # Mongomock does not support $addFields so we need to
    # stub the methods using them.
    def find_latest(self):
        return self._map_fragments(
            self._mongo_repository.get_collection().find({})
        )

    # Mongomock does not support $concat so we need to
    # stub the methods using them.
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
def fragment_factory(bibliography):
    return fragment_factory_.FragmentFactory(bibliography)


@pytest.fixture
def fragment_repository(database, fragment_factory):
    return TestFragmentRepository(database, fragment_factory)


@pytest.fixture
def fragmentarium(fragment_repository,
                  changelog,
                  sign_list,
                  dictionary,
                  bibliography):
    return Fragmentarium(fragment_repository,
                         changelog,
                         sign_list,
                         dictionary,
                         bibliography)


class FakeFile:

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
                'read:WGL-folios',
                'read:bibliography',
                'write:bibliography',
                'read:texts',
                'write:texts',
                'create:texts'
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
            text_repository,
            changelog,
            bibliography,
            user):
    return {
        'auth_backend': NoneAuthBackend(lambda: user),
        'dictionary': dictionary,
        'sign_repository': sign_repository,
        'files': file_repository,
        'fragment_repository': fragment_repository,
        'changelog': changelog,
        'bibliography': bibliography,
        'text_repository': text_repository
    }


@pytest.fixture
def client(context):
    api = ebl.app.create_app(context)
    return testing.TestClient(api)


@pytest.fixture
def guest_client(context):
    api = ebl.app.create_app({
        **context,
        'auth_backend': NoneAuthBackend(lambda: None),
    })
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
        "pos": ["V"]
    }


@pytest.fixture
def lemmatized_fragment():
    return attr.evolve(
        TransliteratedFragmentFactory.build(),
        text=Text((
            TextLine("1'.", (
                Token('[...'),
                Word('-ku]-nu-ši'),
                Token('[...]')
            )),
            TextLine("2'.", (
                Token('[...]'),
                Word('GI₆', unique_lemma=(UniqueLemma('ginâ I'),)),
                Word('ana', unique_lemma=(UniqueLemma('ana I'),)),
                Word('u₄-š[u', unique_lemma=(UniqueLemma("ūsu I"), )),
                Token('...]')
            )),
            TextLine("3'.", (
                Token('[...'),
                Word('k]i-du', unique_lemma=(UniqueLemma('kīdu I'),)),
                Word('u', unique_lemma=(UniqueLemma('u I'),)),
                Word('ba-ma-t[i', unique_lemma=(UniqueLemma('bamātu I'),)),
                Token('...]')
            )),
            TextLine("6'.", (
                Token('[...]'),
                Word('x'),
                Word('mu', unique_lemma=(UniqueLemma('mu I'),)),
                Word('ta-ma-tu₂', unique_lemma=(UniqueLemma('tamalāku I'),))
            )),
            TextLine("7'.", (
                Word('šu/|BI×IS|'),
            ))
        ))
    )


@pytest.fixture
def another_lemmatized_fragment():
    return attr.evolve(
        TransliteratedFragmentFactory.build(),
        text=Text((
            TextLine("1'.", (
                Word('GI₆', unique_lemma=(UniqueLemma('ginâ I'),)),
                Word('ana', unique_lemma=(UniqueLemma('ana II'), )),
                Word('ana', unique_lemma=(UniqueLemma('ana II'), )),
                Word('u₄-šu', unique_lemma=(UniqueLemma('ūsu I'), ))
            )),
        )),
        signs='MI DIŠ DIŠ UD ŠU'
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


@pytest.fixture
def bibliography_entry():
    return {
        "id": "Q30000000",
        "title": ("The Synergistic Activity of Thyroid Transcription Factor 1 "
                  "and Pax 8 Relies on the Promoter/Enhancer Interplay"),
        "type": "article-journal",
        "DOI": "10.1210/MEND.16.4.0808",
        "issued": {
            "date-parts": [
                [
                    2002,
                    1,
                    1
                ]
            ]
        },
        "PMID": "11923479",
        "volume": "16",
        "page": "837-846",
        "issue": "4",
        "container-title": "Molecular Endocrinology",
        "author": [
            {
                "given": "Stefania",
                "family": "Miccadei"
            },
            {
                "given": "Rossana",
                "family": "De Leo"
            },
            {
                "given": "Enrico",
                "family": "Zammarchi"
            },
            {
                "given": "Pier Giorgio",
                "family": "Natali"
            },
            {
                "given": "Donato",
                "family": "Civitareale"
            }
        ]
    }
