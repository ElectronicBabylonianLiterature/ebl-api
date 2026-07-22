from types import SimpleNamespace
from typing import List, Sequence, cast

from pymongo.errors import PyMongoError

from ebl.fragmentarium.application.realia_info import (
    RealiaInfoSchema,
    resolve_realia_info,
    resolve_realia_info_map,
)
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.named_entity import RealiaEntity
from ebl.fragmentarium.domain.realia_info import RealiaInfo
from ebl.realia.application.realia_repository import RealiaRepository
from ebl.realia.domain.realia_entry import RealiaEntry


class FakeRealiaRepository(RealiaRepository):
    def __init__(self, entries: Sequence[RealiaEntry]) -> None:
        self._entries = {entry.realia_id: entry for entry in entries}
        self.calls: List[List[str]] = []

    def create_indexes(self) -> None:
        raise NotImplementedError()

    def find(self, id_: str) -> RealiaEntry:
        raise NotImplementedError()

    def find_by_realia_id(self, realia_id: str) -> RealiaEntry:
        raise NotImplementedError()

    def search(self, query: str) -> Sequence[RealiaEntry]:
        raise NotImplementedError()

    def find_by_realia_ids(self, realia_ids: Sequence[str]) -> Sequence[RealiaEntry]:
        self.calls.append(list(realia_ids))
        return [self._entries[id_] for id_ in realia_ids if id_ in self._entries]


def make_entry(realia_id: str, lemma: str, type_: Sequence[str]) -> RealiaEntry:
    return RealiaEntry(id=lemma, realia_id=realia_id, type=type_)


def fragment_with_realia(*realia_ids: str) -> Fragment:
    return cast(
        Fragment,
        SimpleNamespace(
            realia=[
                RealiaEntity(id=f"Realia-{index}", realia_id=realia_id)
                for index, realia_id in enumerate(realia_ids)
            ]
        ),
    )


def test_schema_dump():
    info = RealiaInfo("realia_000846", "Apkallu", ("Divine names",))

    assert RealiaInfoSchema().dump(info) == {
        "realiaId": "realia_000846",
        "lemma": "Apkallu",
        "type": ["Divine names"],
    }


def test_schema_load():
    data = {"realiaId": "realia_000846", "lemma": "Apkallu", "type": ["Divine names"]}

    assert RealiaInfoSchema().load(data) == RealiaInfo(
        "realia_000846", "Apkallu", ("Divine names",)
    )


def test_resolve_dedupes_and_projects_sorted():
    repository = FakeRealiaRepository(
        [
            make_entry("realia_000002", "Beta", ("T2",)),
            make_entry("realia_000001", "Alpha", ("T1",)),
        ]
    )
    fragment = fragment_with_realia("realia_000001", "realia_000002", "realia_000001")

    result = resolve_realia_info(fragment, repository)

    assert result == [
        RealiaInfo("realia_000001", "Alpha", ("T1",)),
        RealiaInfo("realia_000002", "Beta", ("T2",)),
    ]
    assert repository.calls == [["realia_000001", "realia_000002"]]


def test_resolve_omits_missing_entries():
    repository = FakeRealiaRepository([make_entry("realia_000001", "Alpha", ("T1",))])
    fragment = fragment_with_realia("realia_000001", "realia_000999")

    assert resolve_realia_info(fragment, repository) == [
        RealiaInfo("realia_000001", "Alpha", ("T1",))
    ]


def test_resolve_empty_without_realia():
    repository = FakeRealiaRepository([])

    assert resolve_realia_info(fragment_with_realia(), repository) == []
    assert repository.calls == []


class FailingRealiaRepository(FakeRealiaRepository):
    def find_by_realia_ids(self, realia_ids: Sequence[str]) -> Sequence[RealiaEntry]:
        raise PyMongoError("realia store unavailable")


def test_resolve_degrades_to_empty_on_infrastructure_failure():
    repository = FailingRealiaRepository([])

    assert resolve_realia_info(fragment_with_realia("realia_000001"), repository) == []


def test_resolve_map_degrades_to_empty_on_infrastructure_failure():
    repository = FailingRealiaRepository([])
    documents = [{"realia": [{"realiaId": "realia_000001"}]}]

    assert resolve_realia_info_map(documents, repository) == {}
