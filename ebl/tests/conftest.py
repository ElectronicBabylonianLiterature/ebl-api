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
import ebl.context
from ebl.auth0 import Auth0User
from ebl.bibliography.application.bibliography import Bibliography
from ebl.bibliography.application.serialization import create_object_entry
from ebl.bibliography.infrastructure.bibliography import MongoBibliographyRepository
from ebl.changelog import Changelog
from ebl.corpus.application.corpus import Corpus
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.dictionary.application.dictionary import Dictionary
from ebl.dictionary.infrastructure.dictionary import MongoWordRepository
from ebl.errors import NotFoundError
from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.application.fragmentarium import Fragmentarium
from ebl.fragmentarium.application.transliteration_update_factory import \
    TransliterationUpdateFactory
from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.fragmentarium.infrastructure.fragment_repository import \
    MongoFragmentRepository
from ebl.signs.application.atf_converter import AtfConverter
from ebl.signs.domain.sign import Sign, SignListRecord, Value
from ebl.signs.infrastructure.mongo_sign_repository import MongoSignRepository


@pytest.fixture
def database():
    return mongomock.MongoClient().ebl


@pytest.fixture
def changelog(database):
    return Changelog(database)


class TestWordRepository(MongoWordRepository):
    # Mongomock does not support $addFields so we need to
    # stub the methods using them.
    def query_by_lemma_prefix(self, _):
        return [self._collection.find_one({})]


@pytest.fixture
def word_repository(database):
    return TestWordRepository(database)


@pytest.fixture
def dictionary(word_repository, changelog):
    return Dictionary(word_repository, changelog)


class TestBibliographyRepository(MongoBibliographyRepository):
    # Mongomock does not support $addFields so we need to
    # stub the methods using them.
    def query_by_author_year_and_title(self, _author=None, _year=None, _title=None):
        return [create_object_entry(
            self._collection.find_one({})
        )]


@pytest.fixture
def bibliography_repository(database):
    return TestBibliographyRepository(database)


@pytest.fixture
def bibliography(bibliography_repository, changelog):
    return Bibliography(bibliography_repository, changelog)


@pytest.fixture
def sign_repository(database):
    return MongoSignRepository(database)


@pytest.fixture
def transliteration_factory(atf_converter):
    return TransliterationUpdateFactory(atf_converter)


@pytest.fixture
def atf_converter(sign_repository):
    return AtfConverter(sign_repository)


@pytest.fixture
def text_repository(database):
    return MongoTextRepository(database,)


@pytest.fixture
def corpus(text_repository, bibliography, changelog, transliteration_factory):
    return Corpus(text_repository,
                  bibliography,
                  changelog,
                  transliteration_factory)


class TestFragmentRepository(MongoFragmentRepository):
    # Mongomock does not support $addFields so we need to
    # stub the methods using them.
    def query_by_transliterated_sorted_by_date(self):
        return self._map_fragments(
            self._collection.find_many({})
        )

    # Mongomock does not support $addFields so we need to
    # stub the methods using them.
    def query_by_transliterated_not_revised_by_other(self):
        return [FragmentInfo.of(fragment)
                for fragment
                in self._map_fragments(
                    self._collection.find_many({})
                )]

    # Mongomock does not support $concat so we need to
    # stub the methods using them.
    def query_next_and_previous_folio(self,
                                      _folio_name,
                                      _folio_number,
                                      _number):
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
def fragmentarium(fragment_repository,
                  changelog,
                  dictionary,
                  bibliography):
    return Fragmentarium(fragment_repository)


@pytest.fixture
def fragment_finder(fragment_repository, dictionary):
    return FragmentFinder(fragment_repository,
                          dictionary)


@pytest.fixture
def fragment_updater(fragment_repository,
                     changelog,
                     bibliography):
    return FragmentUpdater(fragment_repository, changelog, bibliography)


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
def context(word_repository,
            sign_repository,
            file_repository,
            fragment_repository,
            text_repository,
            changelog,
            bibliography_repository,
            user):
    return ebl.context.Context(
        auth_backend=NoneAuthBackend(lambda: user),
        word_repository=word_repository,
        sign_repository=sign_repository,
        files=file_repository,
        fragment_repository=fragment_repository,
        changelog=changelog,
        bibliography_repository=bibliography_repository,
        text_repository=text_repository
    )


@pytest.fixture
def client(context):
    api = ebl.app.create_app(context)
    return testing.TestClient(api)


@pytest.fixture
def guest_client(context):
    api = ebl.app.create_app(attr.evolve(
        context,
        auth_backend=NoneAuthBackend(lambda: None)
    ))
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
        Sign(name,
             tuple(SignListRecord(list_name, number)
                   for list_name, number in lists),
             tuple(Value(value_name, sub_index)
                   for value_name, sub_index in values))
        for name, values, lists in [
            ('KU', [('ku', 1)], [('KWU', '869')]),
            ('NU', [('nu', 1)], [('ABZ', '075')]),
            ('IGI', [('ši', 1)], [('HZL', '288'), ('ABZ', '207a/207b X')]),
            ('DIŠ', [('ana', 1), ('1', 1)], []),
            ('UD', [('u', 4), ('tu', 2)], []),
            ('MI', [('mi', 1), ('gi', 6)], []),
            ('KI', [('ki', 1)], []),
            ('DU', [('du', 1)], []),
            ('U', [('u', 1), ('10', 1)], [('ABZ', '411')]),
            ('|U.U|', [('20', 1)], [('ABZ', '471')]),
            ('BA', [('ba', 1)], []),
            ('MA', [('ma', 1)], []),
            ('TI', [('ti', 1)], []),
            ('MU', [('mu', 1)], []),
            ('TA', [('ta', 1)], []),
            ('ŠU', [('šu', 1)], []),
            ('BU', [('gid', 2)], []),
            ('|(4×ZA)×KUR|', [('geštae', 1)], [('ABZ', '531+588')]),
            ('|(AŠ&AŠ@180)×U|', [], []),
            ('|A.EDIN.LAL|', [('ummu', 3)], []),
            ('|HU.HI|', [('mat', 3)], [('ABZ', '081')]),
            ('AŠ', [('ana', 3)], [('ABZ', '001')]),
            ('EDIN', [('bil', None), ('bir', 4)], [('ABZ', '168')]),
            ('|ŠU₂.3×AN|', [('kunga', 1)], [])
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
