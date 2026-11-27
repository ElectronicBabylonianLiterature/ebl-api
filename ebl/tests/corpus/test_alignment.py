from ebl.corpus.domain.alignment import Alignment, ManuscriptLineAlignment
from ebl.transliteration.domain.alignment import AlignmentToken


def test_number_of_lines() -> None:
    assert (
        Alignment(
            (
                (
                    (
                        ManuscriptLineAlignment((AlignmentToken("ku]-nu-ši", 0),)),
                        ManuscriptLineAlignment((AlignmentToken("ku]-nu-ši", 0),)),
                    ),
                ),
            )
        ).get_number_of_lines()
        == 1
    )


def test_number_of_manuscripts() -> None:
    assert (
        Alignment(
            (
                (
                    (
                        ManuscriptLineAlignment((AlignmentToken("ku]-nu-ši", 0),)),
                        ManuscriptLineAlignment((AlignmentToken("ku]-nu-ši", 0),)),
                    ),
                ),
                ((ManuscriptLineAlignment((AlignmentToken("ku]-nu-ši", 0),)),),),
            )
        ).get_number_of_manuscripts(0, 0)
        == 2
    )


def test_number_of_variants() -> None:
    manuscript = ManuscriptLineAlignment((AlignmentToken("ku]-nu-ši", 0),))

    assert (
        Alignment(
            (((manuscript,), (manuscript,)), ((manuscript,),))
        ).get_number_of_variants(0)
        == 2
    )


def test_manuscript_line() -> None:
    manuscript = ManuscriptLineAlignment((AlignmentToken("ku]-nu-ši", 0),))
    other_manuscript = ManuscriptLineAlignment((AlignmentToken("ku", None),), (1,))

    assert (
        Alignment(
            (((manuscript,),), ((manuscript,), (manuscript, other_manuscript)))
        ).get_manuscript_line(1, 1, 1)
        == other_manuscript
    )
