from ebl.merger import Merger


OLD = [{"key": "a1", "value": 1}, {"key": "b1", "value": 3}]


def inner_merge(old, new):
    return old if old["key"] == new["key"] else new


def map_(entry):
    return entry["key"]


def remove_values(row):
    return [{**entry, "value": None} for entry in row]


def test_merge_empty():
    assert Merger(map_, inner_merge).merge([], []) == []


def test_merge_no_changes():
    assert Merger(map_, inner_merge).merge(OLD, OLD) == OLD


def test_merge_add_line():
    new = [*remove_values(OLD), {"key": "c1", "value": 5}]

    assert Merger(map_, inner_merge).merge(OLD, new) == [*OLD, new[2]]


def test_merge_remove_line():
    new = remove_values(OLD[:1])

    assert Merger(map_, inner_merge).merge(OLD, new) == OLD[:1]


def test_merge_edit_line():
    new = [*remove_values(OLD[:1]), {"key": "b2.1", "value": None}]

    assert Merger(map_, inner_merge).merge(OLD, new) == [
        OLD[0],
        {"key": "b2.1", "value": None},
    ]


def test_merge_edit_lines():
    new = [{"key": "a1.1", "value": None}, {"key": "b1", "value": None}]

    assert Merger(map_, inner_merge).merge(OLD, new) == [
        {"key": "a1.1", "value": None},
        {"key": "b1", "value": 3},
    ]
