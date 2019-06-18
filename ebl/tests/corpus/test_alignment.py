from ebl.corpus.alignment import AlignmentToken, Alignment


def test_alignment():
    assert Alignment.of([
        [
            {
                'value': '-ku]-nu-ši',
                'alignment': 0,
                'hasApparatusEntry': True
            }
        ]
    ]) == Alignment((
        (AlignmentToken('-ku]-nu-ši', 0, True), ),
    ))


def test_only_value():
    assert Alignment.of([
        [
            {
                'value': '-ku]-nu-ši'
            }
        ]
    ]) == Alignment((
        (AlignmentToken('-ku]-nu-ši', None, None), ),
    ))
