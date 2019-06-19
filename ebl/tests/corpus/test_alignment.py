import pytest

from ebl.corpus.alignment import AlignmentToken, Alignment


def test_alignment():
    assert Alignment.from_dict([[[
        {
            'value': 'ku]-nu-ši',
            'alignment': 0,
            'hasApparatusEntry': True
        }
    ]]]) == Alignment((
        (
            (AlignmentToken('ku]-nu-ši', 0, True), ),
        ),
    ))


def test_number_of_lines():
    assert Alignment((
        (
            (AlignmentToken('ku]-nu-ši', 0, True),),
            (AlignmentToken('ku]-nu-ši', 0, True),)
        ),
    )).get_number_of_lines() == 1


def test_number_of_manuscripts():
    assert Alignment((
        (
            (AlignmentToken('ku]-nu-ši', 0, True),),
            (AlignmentToken('ku]-nu-ši', 0, True),)
        ),
        (
            (AlignmentToken('ku]-nu-ši', 0, True),),
        ),
    )).get_number_of_manuscripts(0) == 2


def test_only_value():
    assert Alignment.from_dict([[[
            {
                'value': 'ku]-nu-ši'
            }
    ]]]) == Alignment((
        (
            (AlignmentToken('ku]-nu-ši', None, None), ),
        ),
    ))


def test_missing_apparatus():
    with pytest.raises(ValueError):
        AlignmentToken('bu', 0, None)


def test_missing_alignment():
    with pytest.raises(ValueError):
        AlignmentToken('bu', None, False)
