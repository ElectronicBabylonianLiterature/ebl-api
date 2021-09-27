import datetime
import io
import json
from typing import Any, Mapping, Sequence, Union
import uuid

import attr
import pydash
import pytest
from dictdiffer import diff
from falcon import testing
from falcon_auth import NoneAuthBackend
from marshmallow import EXCLUDE
from pymongo_inmemory import MongoClient

import ebl.app
import ebl.context
from ebl.bibliography.application.bibliography import Bibliography
from ebl.bibliography.application.serialization import create_object_entry
from ebl.bibliography.infrastructure.bibliography import MongoBibliographyRepository
from ebl.changelog import Changelog
from ebl.corpus.application.corpus import Corpus
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.dictionary.application.dictionary import Dictionary
from ebl.dictionary.infrastructure.dictionary import MongoWordRepository
from ebl.files.application.file_repository import File
from ebl.files.infrastructure.grid_fs_file_repository import GridFsFileRepository
from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.application.fragment_matcher import FragmentMatcher
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.application.fragmentarium import Fragmentarium
from ebl.fragmentarium.application.transliteration_update_factory import (
    TransliterationUpdateFactory,
)
from ebl.fragmentarium.infrastructure.fragment_repository import MongoFragmentRepository
from ebl.fragmentarium.infrastructure.mongo_annotations_repository import (
    MongoAnnotationsRepository,
)
from ebl.lemmatization.infrastrcuture.mongo_suggestions_finder import (
    MongoLemmaRepository,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory
from ebl.transliteration.domain.sign import Sign, SignListRecord, Value
from ebl.signs.infrastructure.mongo_sign_repository import (
    MongoSignRepository,
    SignSchema,
)
from ebl.users.domain.user import User
from ebl.users.infrastructure.auth0 import Auth0User


@pytest.fixture(scope="session")
def mongo_client() -> MongoClient:
    return MongoClient()


@pytest.fixture
def database(mongo_client: MongoClient):
    database = str(uuid.uuid4())
    yield mongo_client[database]
    mongo_client.drop_database(database)


@pytest.fixture
def changelog(database):
    return Changelog(database)


class TestWordRepository(MongoWordRepository):
    # Mongomock does not support $substrCP so we need to
    # stub the methods using it.
    def query_by_lemma_prefix(self, _):
        return [self._collection.find_one({})]


@pytest.fixture
def word_repository(database):
    return TestWordRepository(database)


@pytest.fixture
def dictionary(word_repository, changelog):
    return Dictionary(word_repository, changelog)


class TestBibliographyRepository(MongoBibliographyRepository):
    # Mongomock does not support $substrCP so we need to
    # stub the methods using it.
    def query_by_author_year_and_title(
        self, _author=None, _year=None, _title=None, _greater_than=False
    ):
        return [create_object_entry(self._collection.find_one({}))]


class TestSignRepository(MongoSignRepository):
    # Mongomock does not support $let in lookup so we need to
    # stub the methods using it.
    # https://github.com/mongomock/mongomock/issues/536

    def search_composite_signs(self, reading: str, sub_index: int) -> Sequence[Sign]:
        return [SignSchema(unknown=EXCLUDE).load(self._collection.find_one({}))]


@pytest.fixture
def bibliography_repository(database):
    return TestBibliographyRepository(database)


@pytest.fixture
def bibliography(bibliography_repository, changelog):
    return Bibliography(bibliography_repository, changelog)


@pytest.fixture
def sign_repository(database):
    return TestSignRepository(database)


@pytest.fixture
def transliteration_factory(sign_repository):
    return TransliterationUpdateFactory(sign_repository)


@pytest.fixture
def text_repository(database):
    return MongoTextRepository(database)


@pytest.fixture
def corpus(
    text_repository, bibliography, changelog, transliteration_factory, sign_repository
):
    return Corpus(text_repository, bibliography, changelog, sign_repository)


@pytest.fixture
def fragment_repository(database):
    return MongoFragmentRepository(database)


@pytest.fixture
def fragmentarium(fragment_repository, changelog, dictionary, bibliography):
    return Fragmentarium(fragment_repository)


@pytest.fixture
def fragment_finder(
    fragment_repository, dictionary, photo_repository, file_repository, bibliography
):
    return FragmentFinder(
        bibliography, fragment_repository, dictionary, photo_repository, file_repository
    )


@pytest.fixture
def fragment_matcher(fragment_repository):
    return FragmentMatcher(fragment_repository)


@pytest.fixture
def fragment_updater(fragment_repository, changelog, bibliography, photo_repository):
    return FragmentUpdater(
        fragment_repository, changelog, bibliography, photo_repository
    )


class FakeFile(File):
    def __init__(self, filename: str, data: bytes, metadata: dict):
        self.filename = filename
        self.data = data
        self._content_type = "image/jpeg"
        self._file = io.BytesIO(data)
        self._metadata = metadata

    @property
    def length(self) -> int:
        return len(self.data)

    @property
    def content_type(self) -> str:
        return self._content_type

    @property
    def metadata(self) -> Mapping[str, Any]:
        return self._metadata

    def close(self) -> None:
        self._file.close()

    def read(self, size=-1):
        return self._file.read(size)


class TestFilesRepository(GridFsFileRepository):
    def __init__(self, database, bucket: str, *files: FakeFile):
        super().__init__(database, bucket)
        for file in files:
            self._create(file)

    def _create(self, file: FakeFile) -> None:
        self._fs.put(
            file,
            filename=file.filename,
            contentType=file.content_type,
            metadata=file.metadata,
        )


@pytest.fixture
def file():
    return FakeFile("image.jpg", b"oyoFLAbXbR", {})


@pytest.fixture
def file_repository(database, file):
    return TestFilesRepository(database, "fs", file)


@pytest.fixture
def folio_with_allowed_scope():
    return FakeFile("WGL_001.jpg", b"ZTbvOTqvSW", {"scope": "WGL-folios"})


@pytest.fixture
def folio_with_restricted_scope():
    return FakeFile("AKG_001.jpg", b"klgsFPOutx", {"scope": "AKG-folios"})


@pytest.fixture
def folio_repository(database, folio_with_allowed_scope, folio_with_restricted_scope):
    return TestFilesRepository(
        database, "folios", folio_with_allowed_scope, folio_with_restricted_scope
    )


@pytest.fixture
def photo():
    return FakeFile("K.1.jpg", b"yVGSDbnTth", {})


@pytest.fixture
def photo_repository(database, photo):
    return TestFilesRepository(database, "photos", photo)


@pytest.fixture
def annotations_repository(database):
    return MongoAnnotationsRepository(database)


@pytest.fixture
def lemma_repository(database):
    return MongoLemmaRepository(database)


@pytest.fixture
def user() -> User:
    return Auth0User(
        {
            "scope": [
                "read:words",
                "write:words",
                "transliterate:fragments",
                "lemmatize:fragments",
                "annotate:fragments",
                "read:fragments",
                "read:WGL-folios",
                "read:bibliography",
                "write:bibliography",
                "read:texts",
                "write:texts",
                "create:texts",
            ]
        },
        lambda: {
            "name": "test.user@example.com",
            "https://ebabylon.org/eblName": "User",
        },
    )


@pytest.fixture
def context(
    word_repository,
    sign_repository,
    file_repository,
    photo_repository,
    folio_repository,
    fragment_repository,
    text_repository,
    changelog,
    bibliography_repository,
    annotations_repository,
    lemma_repository,
    database,
    user,
):
    return ebl.context.Context(
        auth_backend=NoneAuthBackend(lambda: user),
        word_repository=word_repository,
        sign_repository=sign_repository,
        public_file_repository=file_repository,
        photo_repository=photo_repository,
        folio_repository=folio_repository,
        fragment_repository=fragment_repository,
        changelog=changelog,
        bibliography_repository=bibliography_repository,
        text_repository=text_repository,
        annotations_repository=annotations_repository,
        lemma_repository=lemma_repository,
    )


@pytest.fixture
def client(context):
    api = ebl.app.create_app(context)
    return testing.TestClient(api)


@pytest.fixture
def guest_client(context):
    api = ebl.app.create_app(
        attr.evolve(context, auth_backend=NoneAuthBackend(lambda: None))
    )
    return testing.TestClient(api)


@pytest.fixture
def word():
    return {
        "lemma": ["part1", "part2"],
        "attested": True,
        "legacyLemma": "part1 part2",
        "homonym": "I",
        "_id": "part1 part2 I",
        "forms": [
            {"lemma": ["form1"], "notes": [], "attested": True},
            {"lemma": ["form2", "part2"], "notes": ["a note"], "attested": False},
        ],
        "meaning": "a meaning",
        "amplifiedMeanings": [
            {
                "meaning": "(*i/i*) meaning",
                "vowels": [{"value": ["i", "i"], "notes": []}],
                "key": "G",
                "entries": [],
            }
        ],
        "logograms": [],
        "derived": [[{"lemma": ["derived"], "homonym": "I", "notes": []}]],
        "derivedFrom": None,
        "source": "**part1 part2** source",
        "roots": ["wb'", "'b'"],
        "pos": ["V"],
        "guideWord": "meaning",
        "oraccWords": [{"lemma": "oracc lemma", "guideWord": "oracc meaning"}],
        "origin": "test",
        "akkadischeGlossareUndIndices": [
            {
                "mainWord" = "word",
                "note" = "a note",
                "reference" = "reference",
                "AfO" = "AfO",
                "agiID" = "agiID",
            }
        ],
    }


@pytest.fixture
def make_changelog_entry(user):
    def _make_changelog_entry(resource_type, resource_id, old, new):
        return {
            "user_profile": {
                key.replace(".", "_"): value for key, value in user.profile.items()
            },
            "resource_type": resource_type,
            "resource_id": resource_id,
            "date": datetime.datetime.utcnow().isoformat(),
            "diff": json.loads(json.dumps(list(diff(old, new)))),
        }

    return _make_changelog_entry


@pytest.fixture
def signs():
    return [
        Sign(
            name,
            tuple(SignListRecord(list_name, number) for list_name, number in lists),
            tuple(Value(value_name, sub_index) for value_name, sub_index in values),
        )
        for name, values, lists in [
            ("P₂", [(":", 1)], [("ABZ", "377n1")]),
            ("KU", [("ku", 1)], [("KWU", "869")]),
            ("NU", [("nu", 1)], [("ABZ", "075")]),
            ("IGI", [("ši", 1)], [("HZL", "288"), ("ABZ", "207a/207b X")]),
            ("DIŠ", [("ana", 1), ("1", 1)], []),
            ("UD", [("u", 4), ("tu", 2)], []),
            ("MI", [("mi", 1), ("gi", 6)], []),
            ("KI", [("ki", 1)], []),
            ("DU", [("du", 1)], []),
            ("U", [("u", 1), ("10", 1)], [("ABZ", "411")]),
            ("|U.U|", [("20", 1)], [("ABZ", "471")]),
            ("BA", [("ba", 1), ("ku", 1)], []),
            ("MA", [("ma", 1)], []),
            ("TI", [("ti", 1)], []),
            ("MU", [("mu", 1)], []),
            ("TA", [("ta", 1)], []),
            ("ŠU", [("šu", 1)], []),
            ("BU", [("gid", 2)], []),
            ("|(4×ZA)×KUR|", [("geštae", 1)], [("ABZ", "531+588")]),
            ("|(AŠ&AŠ@180)×U|", [], []),
            ("|A.EDIN.LAL|", [("ummu", 3)], []),
            ("|HU.HI|", [("mat", 3)], [("ABZ", "081")]),
            ("AŠ", [("ana", 3)], [("ABZ", "001")]),
            ("EDIN", [("bil", None), ("bir", 4)], [("ABZ", "168")]),
            ("|ŠU₂.3×AN|", [("kunga", 1)], []),
        ]
    ]


@pytest.fixture
def create_mongo_bibliography_entry():
    def _from_bibliography_entry(bibliography_entry: Union[dict, None] = None) -> dict:
        if not bibliography_entry:
            bibliography_entry = BibliographyEntryFactory.build()
        return pydash.map_keys(
            bibliography_entry, lambda _, key: "_id" if key == "id" else key
        )

    return _from_bibliography_entry
