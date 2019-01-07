from ebl.merger import Merger


OLD = [
    [{'key': 'a1', 'value': 1}, {'key': 'a2', 'value': 2}],
    [{'key': 'b1', 'value': 3}, {'key': 'b2', 'value': 4}]
]


def map_(entry):
    return entry['key']


def remove_values(rows):
    return [
        [{
            **entry,
            'value': None
        } for entry in row]
        for row in rows
    ]


def test_merge_empty():
    assert Merger(map_, 2).merge([], []) == []


def test_merge_no_changes():
    assert Merger(map_, 2).merge(OLD, OLD) == OLD


def test_merge_add_line():
    new = [
        *remove_values(OLD),
        [{'key': 'c1', 'value': 5}, {'key': 'c2', 'value': 6}]
    ]

    assert Merger(map_, 2).merge(OLD, new) == [
        *OLD,
        new[2]
    ]


def test_merge_remove_line():
    new = remove_values(OLD[:1])

    assert Merger(map_, 2).merge(OLD, new) == OLD[:1]


def test_merge_edit_line():
    new = [
        *remove_values(OLD[:1]),
        [{'key': 'b1', 'value': None}, {'key': 'b2.1', 'value': None}]
    ]

    assert Merger(map_, 2).merge(OLD, new) == [
        OLD[0],
        [{'key': 'b1', 'value': 3}, {'key': 'b2.1', 'value': None}]
    ]


def test_merge_edit_lines():
    new = [
        [{'key': 'a1.1', 'value': None}, {'key': 'a2', 'value': None}],
        [{'key': 'b1', 'value': None}, {'key': 'b2.1', 'value': None}]
    ]

    assert Merger(map_, 2).merge(OLD, new) == [
        [{'key': 'a1.1', 'value': None}, {'key': 'a2', 'value': 2}],
        [{'key': 'b1', 'value': 3}, {'key': 'b2.1', 'value': None}]
    ]


def test_merge_inner_merge():
    assert Merger(
        lambda x: f' {x} ',
        inner_merge=lambda state: state.previous_old + state.current_new
    ).merge([1, 2], [1, 3]) == [1, 5]
