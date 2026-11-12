import io
from pathlib import Path
from typing import Any, Mapping, Union

import pytest
from PIL import Image


from ebl.files.application.file_repository import File
from ebl.files.infrastructure.grid_fs_file_repository import GridFsFileRepository
from ebl.fragmentarium.application.fragment_finder import ThumbnailSize
from ebl.transliteration.domain.museum_number import MuseumNumber


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
    image = Image.open(Path(__file__).parent.parent.resolve() / "test_image.jpeg")
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
