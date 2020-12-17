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
