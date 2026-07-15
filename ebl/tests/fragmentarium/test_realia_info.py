from types import SimpleNamespace

from ebl.fragmentarium.application.realia_info import (
    RealiaInfoSchema,
    resolve_realia_info,
)
from ebl.fragmentarium.domain.named_entity import RealiaEntity
from ebl.fragmentarium.domain.realia_info import RealiaInfo
from ebl.realia.domain.realia_entry import RealiaEntry


class FakeRealiaRepository:
    def __init__(self, entries):
        self._entries = {entry.realia_id: entry for entry in entries}
        self.calls = []

    def find_by_realia_ids(self, realia_ids):
        self.calls.append(list(realia_ids))
        return [self._entries[id_] for id_ in realia_ids if id_ in self._entries]


def make_entry(realia_id, lemma, type_):
    return RealiaEntry(id=lemma, realia_id=realia_id, type=type_)


def fragment_with_realia(*realia_ids):
    return SimpleNamespace(
        realia=[
            RealiaEntity(id=f"Realia-{index}", realia_id=realia_id)
            for index, realia_id in enumerate(realia_ids)
        ]
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
