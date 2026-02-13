import datetime
import io
import json
import os
import uuid
from pathlib import Path
from typing import Any, List, Mapping, Sequence, Union

import attr
import pydash
import pytest
from PIL import Image
from dictdiffer import diff

from falcon import testing
from falcon_auth import NoneAuthBackend
from falcon_caching import Cache
from marshmallow import EXCLUDE
from pymongo.database import Database
from pymongo import MongoClient

import ebl.app
import ebl.context
from ebl.bibliography.application.bibliography import Bibliography
from ebl.bibliography.application.serialization import create_object_entry
from ebl.bibliography.infrastructure.bibliography import MongoBibliographyRepository
from ebl.cache.application.custom_cache import ChapterCache
from ebl.cache.infrastructure.mongo_cache_repository import MongoCacheRepository
from ebl.changelog import Changelog
from ebl.corpus.application.corpus import Corpus, CorpusDependencies
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.dictionary.application.dictionary_service import Dictionary
from ebl.dictionary.infrastructure.word_repository import MongoWordRepository
from ebl.ebl_ai_client import EblAiClient
from ebl.files.application.file_repository import File
from ebl.files.infrastructure.grid_fs_file_repository import GridFsFileRepository
from ebl.fragmentarium.application.annotations_service import AnnotationsService
from ebl.fragmentarium.application.fragment_finder import FragmentFinder, ThumbnailSize
from ebl.fragmentarium.application.fragment_matcher import FragmentMatcher
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.application.fragmentarium import Fragmentarium
from ebl.fragmentarium.application.transliteration_update_factory import (
    TransliterationUpdateFactory,
)
from ebl.fragmentarium.domain.named_entity import EntityAnnotationSpan, NamedEntityType
from ebl.fragmentarium.infrastructure.cropped_sign_images_repository import (
    MongoCroppedSignImagesRepository,
)
from ebl.fragmentarium.infrastructure.mongo_annotations_repository import (
    MongoAnnotationsRepository,
)
from ebl.fragmentarium.infrastructure.mongo_fragment_repository import (
    MongoFragmentRepository,
)
from ebl.fragmentarium.infrastructure.mongo_findspot_repository import (
    MongoFindspotRepository,
)
from ebl.lemmatization.infrastrcuture.mongo_suggestions_finder import (
    MongoLemmaRepository,
)
from ebl.signs.infrastructure.mongo_sign_repository import (
    MongoSignRepository,
    SignSchema,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory
from ebl.transliteration.application.parallel_line_injector import ParallelLineInjector
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.at_line import ColumnAtLine, SurfaceAtLine, ObjectAtLine
from ebl.transliteration.domain.labels import ColumnLabel, SurfaceLabel, ObjectLabel
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.sign import (
    Sign,
    SignListRecord,
    SortKeys,
    Value,
    Logogram,
)
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.word_tokens import Word
from ebl.transliteration.infrastructure.mongo_parallel_repository import (
    MongoParallelRepository,
)
from ebl.afo_register.infrastructure.mongo_afo_register_repository import (
    MongoAfoRegisterRepository,
)
from ebl.dossiers.infrastructure.mongo_dossiers_repository import (
    MongoDossiersRepository,
)
from ebl.common.application.provenance_service import ProvenanceService
from ebl.common.domain.provenance_data import build_provenance_records
from ebl.common.infrastructure.mongo_provenance_repository import (
    MongoProvenanceRepository,
)
from ebl.users.domain.user import Guest, User
from ebl.users.infrastructure.auth0 import Auth0User
from ebl.fragmentarium.web.annotations import AnnotationResource
from ebl.tests.factories.archaeology import FindspotFactory, FINDSPOT_COUNT


@pytest.fixture(scope="session")
def mongo_client() -> MongoClient:
    if os.getenv("CI") == "true":
        return MongoClient(os.environ["MONGODB_URI"])
    else:
        os.environ.setdefault("PYMONGOIM__OPERATING_SYSTEM", "ubuntu")
        os.environ.setdefault("PYMONGOIM__OS_VERSION", "20")

        from pymongo_inmemory import MongoClient as InMemoryMongoClient

        return InMemoryMongoClient()


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


@pytest.fixture
def cropped_sign_images_repository(database):
    return MongoCroppedSignImagesRepository(database)


@pytest.fixture
def mongo_cache_repository(database):
    return MongoCacheRepository(database)


@pytest.fixture
def ebl_ai_client():
    return EblAiClient("http://localhost:8001")


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
def parallel_repository(database: Database) -> MongoParallelRepository:
    return MongoParallelRepository(database)


@pytest.fixture
def parallel_line_injector(
    parallel_repository: MongoParallelRepository,
) -> ParallelLineInjector:
    return ParallelLineInjector(parallel_repository)


@pytest.fixture
def text_repository(database: Database, seeded_provenance_service):
    return MongoTextRepository(database, seeded_provenance_service)


@pytest.fixture
def corpus_dependencies(request: pytest.FixtureRequest) -> CorpusDependencies:
    return CorpusDependencies(
        repository=request.getfixturevalue("text_repository"),
        bibliography=request.getfixturevalue("bibliography"),
        changelog=request.getfixturevalue("changelog"),
        sign_repository=request.getfixturevalue("sign_repository"),
        parallel_line_injector=request.getfixturevalue("parallel_line_injector"),
        provenance_service=request.getfixturevalue("seeded_provenance_service"),
    )


@pytest.fixture
def corpus(corpus_dependencies: CorpusDependencies) -> Corpus:
    return Corpus(corpus_dependencies)


@pytest.fixture
def fragment_repository(database, seeded_provenance_service):
    return MongoFragmentRepository(database, seeded_provenance_service)


@pytest.fixture
def findspot_repository(database, seeded_provenance_service):
    return MongoFindspotRepository(database, seeded_provenance_service)


@pytest.fixture
def findspots():
    return FindspotFactory.build_batch(FINDSPOT_COUNT)


@pytest.fixture
def fragmentarium(fragment_repository):
    return Fragmentarium(fragment_repository)


@pytest.fixture
def fragment_finder(
    fragment_repository,
    dictionary,
    photo_repository,
    file_repository,
    thumbnail_repository,
    bibliography,
    parallel_line_injector,
):
    return FragmentFinder(
        bibliography,
        fragment_repository,
        dictionary,
        photo_repository,
        file_repository,
        thumbnail_repository,
        parallel_line_injector,
    )


@pytest.fixture
def fragment_matcher(fragment_repository):
    return FragmentMatcher(fragment_repository)


@pytest.fixture
def fragment_updater(
    fragment_repository,
    changelog,
    bibliography,
    photo_repository,
    parallel_line_injector,
):
    return FragmentUpdater(
        fragment_repository,
        changelog,
        bibliography,
        photo_repository,
        parallel_line_injector,
    )


@pytest.fixture
def afo_register_repository(database):
    return MongoAfoRegisterRepository(database)


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
    return FakeFile("ILF_001.jpg", b"klgsFPOutx", {"scope": "ILF-folios"})


@pytest.fixture
def folio_repository(database, folio_with_allowed_scope, folio_with_restricted_scope):
    return TestFilesRepository(
        database, "folios", folio_with_allowed_scope, folio_with_restricted_scope
    )


@pytest.fixture
def photo():
    return FakeFile("K.1.jpg", b"yVGSDbnTth", {})


def create_test_photo(number: Union[MuseumNumber, str]):
    image = Image.open(Path(__file__).parent.resolve() / "test_image.jpeg")
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return FakeFile(f"{number}.jpg", buf.getvalue(), {})


@pytest.fixture
def photo_repository(database, photo):
    return TestFilesRepository(database, "photos", photo, create_test_photo("K.2"))


@pytest.fixture
def thumbnail_repository(database, photo):
    thumbnails = [
        FakeFile(
            photo.filename.replace(".jpg", f"_{resolution.value}.jpg"),
            b"yVGSDbnTth",
            {},
        )
        for resolution in ThumbnailSize
    ]
    return TestFilesRepository(database, "thumbnails", photo, *thumbnails)


@pytest.fixture
def annotations_repository(database):
    return MongoAnnotationsRepository(database)


@pytest.fixture
def lemma_repository(database):
    return MongoLemmaRepository(database)


@pytest.fixture
def annotations_service(
    annotations_repository,
    photo_repository,
    changelog,
    fragment_repository,
    cropped_sign_images_repository,
):
    return AnnotationsService(
        EblAiClient(""),
        annotations_repository,
        photo_repository,
        changelog,
        fragment_repository,
        photo_repository,
        cropped_sign_images_repository,
    )


@pytest.fixture
def user() -> User:
    return Auth0User(
        {
            "scope": " ".join(
                [
                    "read:words",
                    "write:words",
                    "transliterate:fragments",
                    "lemmatize:fragments",
                    "annotate:fragments",
                    "read:CAIC-fragments",
                    "read:SIPPARLIBRARY-fragments",
                    "read:ITALIANNINEVEH-fragments",
                    "read:URUKLBU-fragments",
                    "read:WGL-folios",
                    "read:bibliography",
                    "write:bibliography",
                    "read:texts",
                    "write:texts",
                    "create:texts",
                    "write:provenances",
                ]
            )
        },
        lambda: {
            "name": "test.user@example.com",
            "https://ebabylon.org/eblName": "User",
        },
    )


@pytest.fixture
def dossiers_repository(database, seeded_provenance_service):
    return MongoDossiersRepository(database, seeded_provenance_service)


@pytest.fixture
def provenance_repository(database):
    return MongoProvenanceRepository(database)


@pytest.fixture
def provenance_service(provenance_repository):
    return ProvenanceService(provenance_repository)


@pytest.fixture
def seeded_provenance_service(provenance_repository):
    for record in build_provenance_records():
        provenance_repository.create(record)
    return ProvenanceService(provenance_repository)


@pytest.fixture
def context(request: pytest.FixtureRequest) -> ebl.context.Context:
    return ebl.context.Context(
        ebl_ai_client=request.getfixturevalue("ebl_ai_client"),
        auth_backend=NoneAuthBackend(lambda: request.getfixturevalue("user")),
        cropped_sign_images_repository=request.getfixturevalue(
            "cropped_sign_images_repository"
        ),
        word_repository=request.getfixturevalue("word_repository"),
        sign_repository=request.getfixturevalue("sign_repository"),
        public_file_repository=request.getfixturevalue("file_repository"),
        photo_repository=request.getfixturevalue("photo_repository"),
        folio_repository=request.getfixturevalue("folio_repository"),
        thumbnail_repository=request.getfixturevalue("thumbnail_repository"),
        fragment_repository=request.getfixturevalue("fragment_repository"),
        changelog=request.getfixturevalue("changelog"),
        bibliography_repository=request.getfixturevalue("bibliography_repository"),
        provenance_repository=request.getfixturevalue("provenance_repository"),
        provenance_service=request.getfixturevalue("seeded_provenance_service"),
        text_repository=request.getfixturevalue("text_repository"),
        annotations_repository=request.getfixturevalue("annotations_repository"),
        lemma_repository=request.getfixturevalue("lemma_repository"),
        afo_register_repository=request.getfixturevalue("afo_register_repository"),
        dossiers_repository=request.getfixturevalue("dossiers_repository"),
        findspot_repository=request.getfixturevalue("findspot_repository"),
        cache=Cache({"CACHE_TYPE": "null"}),
        custom_cache=ChapterCache(request.getfixturevalue("mongo_cache_repository")),
        parallel_line_injector=request.getfixturevalue("parallel_line_injector"),
    )


@pytest.fixture
def client(context):
    api = ebl.app.create_app(context)
    return testing.TestClient(api)


class EnsureAnnotationPost:
    def on_post(self, req, resp):
        return AnnotationResource(annotations_service).on_post(req, resp, "K.123")


@pytest.fixture
def guest_client(context):
    api = ebl.app.create_app(attr.evolve(context, auth_backend=NoneAuthBackend(Guest)))
    api.add_route("/fragments/K.123/annotations", EnsureAnnotationPost())
    return testing.TestClient(api)


@pytest.fixture
def cached_client(context):
    api = ebl.app.create_app(
        attr.evolve(
            context,
            cache=Cache(config={"CACHE_TYPE": "simple"}),
        )
    )
    return testing.TestClient(api)


@pytest.fixture
def text_with_labels():
    return Text.of_iterable(
        [
            TextLine.of_iterable(LineNumber(1), [Word.of([Reading.of_name("bu")])]),
            ColumnAtLine(ColumnLabel.from_int(1)),
            SurfaceAtLine(SurfaceLabel([], atf.Surface.SURFACE, "Stone wig")),
            ObjectAtLine(ObjectLabel([], atf.Object.OBJECT, "Stone wig")),
            TextLine.of_iterable(LineNumber(2), [Word.of([Reading.of_name("bu")])]),
        ]
    )


@pytest.fixture
def word():
    return {
        "lemma": ["part1", "Parṭ2"],
        "attested": True,
        "legacyLemma": "part1 part2",
        "homonym": "I",
        "_id": "part1 part2 I",
        "forms": [
            {"lemma": ["form1"], "notes": [], "attested": True},
            {"lemma": ["form2", "part2"], "notes": ["a note"], "attested": False},
        ],
        "meaning": "some semantics",
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
        "roots": ["wb'", "'b'", "plš"],
        "pos": ["V"],
        "guideWord": "meaning",
        "arabicGuideWord": "meaning",
        "oraccWords": [{"lemma": "oracc lemma", "guideWord": "oracc meaning"}],
        "origin": ["CDA"],
        "akkadischeGlossareUndIndices": [
            {
                "mainWord": "word",
                "note": "a note",
                "reference": "reference",
                "AfO": "AfO",
                "agiID": "agiID",
            }
        ],
        "cdaAddenda": "additions",
        "supplementsAkkadianDictionaries": "new stuff",
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
            name=name,
            lists=tuple(
                SignListRecord(list_name, number) for list_name, number in lists
            ),
            values=tuple(
                Value(value_name, sub_index) for value_name, sub_index in values
            ),
            logograms=tuple(
                Logogram(name, name, tuple(word_ids), name) for word_ids in logograms
            ),
            unicode=tuple(unicode),
            sort_keys=SortKeys(*sort_keys) if sort_keys else None,
        )
        for name, values, lists, logograms, unicode, sort_keys in [
            (
                "P₂",
                [(":", 1)],
                [("ABZ", "377n1")],
                [["lemmatu I"]],
                [74865],
                ([1, 2], [1, 2], [1, 2], [1, 2]),
            ),
            ("KU", [("ku", 1)], [("KWU", "869")], [], [74154], None),
            ("NU", [("nu", 1)], [("ABZ", "075")], [], [74337], None),
            (
                "IGI",
                [("ši", 1), ("igi", 1)],
                [("HZL", "288"), ("ABZ", "207a/207b X")],
                [],
                [74054],
                None,
            ),
            ("DIŠ", [("ana", 1), ("1", 1), ("diš", 1)], [], [], [73849], None),
            ("UD", [("ud", 1), ("u", 4), ("tu", 2)], [], [], [74515], None),
            ("MI", [("mi", 1), ("gi", 6)], [], [], [74282], None),
            ("KI", [("ki", 1)], [], [], [74144], None),
            ("DU", [("du", 1)], [], [], [73850], None),
            ("U", [("u", 1), ("10", 1)], [("ABZ", "411")], [], [74507], None),
            ("|U.U|", [("20", 1)], [("ABZ", "471")], [], [74649], None),
            ("BA", [("ba", 1), ("ku", 1)], [], [], [73792], None),
            ("MA", [("ma", 1)], [], [], [74272], None),
            ("TI", [("ti", 1)], [], [], [74494], None),
            ("MU", [("mu", 1)], [], [], [74284], None),
            ("TA", [("ta", 1)], [], [], [74475], None),
            ("ŠU", [("šu", 1)], [], [], [74455], None),
            ("BU", [("bu", 1), ("gid", 2)], [], [], [73805], None),
            ("|(4×ZA)×KUR|", [("geštae", 1)], [("ABZ", "531+588")], [], [74591], None),
            ("|(AŠ&AŠ@180)×U|", [], [], [], [74499], None),
            ("|A.EDIN.LAL|", [("ummu", 3)], [], [], [73728, 73876, 74226], None),
            ("|HU.HI|", [("mat", 3)], [("ABZ", "081")], [], [74039, 74029], None),
            ("AŠ", [("ana", 3)], [("ABZ", "001")], [], [73784], None),
            ("EDIN", [("bil", None), ("bir", 4)], [("ABZ", "168")], [], [73876], None),
            ("|ŠU₂.3×AN|", [("kunga", 1)], [], [], [74457], None),
            ("BUR₂", [("bul", 1)], [("ABZ", "11")], [], [74215], None),
            ("HU", [("u", 18)], [("ABZ", "78")], [], [74039], None),
            ("|URU×URUDA|", [("bansur", 1)], [("ABZ", "41")], [], [74574], None),
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


@pytest.fixture
def named_entity_spans() -> List[EntityAnnotationSpan]:
    return [
        EntityAnnotationSpan("Entity-1", NamedEntityType.PERSONAL_NAME, ["Word-2"]),
        EntityAnnotationSpan(
            "Entity-2", NamedEntityType.BUILDING_NAME, ["Word-2", "Word-3"]
        ),
        EntityAnnotationSpan(
            "Entity-3", NamedEntityType.YEAR_NAME, ["Word-7", "Word-14"]
        ),
    ]
