from ebl.errors import NotFoundError
from ebl.files.application.file_repository import File, FileRepository


class StubFile(File):
    @property
    def metadata(self):
        return {}

    @property
    def length(self) -> int:
        return 0

    @property
    def content_type(self) -> str:
        return "image/jpeg"

    def read(self, size=-1) -> bytes:
        return b""

    def close(self) -> None:
        return None


class StubFileRepository(FileRepository):
    def __init__(self, known_file_name: str):
        self._known_file_name = known_file_name

    def query_by_file_name(self, file_name: str) -> File:
        if file_name != self._known_file_name:
            raise NotFoundError(f"File {file_name} not found.")
        return StubFile()


def test_an_existing_file_is_reported_as_present():
    assert StubFileRepository("K.1.jpg").query_if_file_exists("K.1.jpg")


def test_a_missing_file_is_reported_as_absent():
    assert not StubFileRepository("K.1.jpg").query_if_file_exists("K.2.jpg")


def test_the_file_contract_is_abstract():
    assert File.__abstractmethods__ == frozenset(
        {"metadata", "length", "content_type", "read", "close"}
    )


def test_the_repository_contract_is_abstract():
    assert FileRepository.__abstractmethods__ == frozenset({"query_by_file_name"})


def test_a_file_has_no_authorization_responsibility():
    assert not hasattr(StubFile(), "can_be_read_by")
