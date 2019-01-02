from ebl.merger import Differ


def test_diff_one_dimension():
    old = [{'value': 'a'}, {'value': 'b'}]
    new = [{'value': 'a'}, {'value': 'c'}]
    diff = Differ(lambda entry: entry['value'], 1).diff(old, new)

    assert list(diff) == ['  a', '- b', '+ c']


def test_diff_two_dimensions():
    old = [
        [{'value': 'a'}, {'value': 'aa'}],
        [{'value': 'b'}, {'value': 'bb'}]
    ]
    new = [
        [{'value': 'a'}, {'value': 'aa'}],
        [{'value': 'c'}, {'value': 'bb'}]
    ]
    diff = Differ(lambda entry: entry['value'], 2).diff(old, new)

    assert list(diff) == ['  a aa', '- b bb', '? ^\n', '+ c bb', '? ^\n']
