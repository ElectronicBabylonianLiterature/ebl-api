from ebl.transliteration.domain.alignment import Alignment, AlignmentToken


def test_alignment():
    assert Alignment.from_dict([[[
        {
            'value': 'ku]-nu-ši',
            'alignment': 0
        }
    ]]]) == Alignment((
        (
            (AlignmentToken('ku]-nu-ši', 0), ),
        ),
    ))


def test_number_of_lines():
    assert Alignment((
        (
            (AlignmentToken('ku]-nu-ši', 0),),
            (AlignmentToken('ku]-nu-ši', 0),)
        ),
    )).get_number_of_lines() == 1


def test_number_of_manuscripts():
    assert Alignment((
        (
            (AlignmentToken('ku]-nu-ši', 0),),
            (AlignmentToken('ku]-nu-ši', 0),)
        ),
        (
            (AlignmentToken('ku]-nu-ši', 0),),
        ),
    )).get_number_of_manuscripts(0) == 2


def test_only_value():
    assert Alignment.from_dict([[[
            {
                'value': 'ku]-nu-ši'
            }
    ]]]) == Alignment((
        (
            (AlignmentToken('ku]-nu-ši', None), ),
        ),
    ))
