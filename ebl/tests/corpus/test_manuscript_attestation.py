import attr
import pytest
from ebl.corpus.domain.manuscript_attestation import ManuscriptAttestation
from ebl.tests.factories.corpus import (
    TextFactory,
    ChapterFactory,
    ManuscriptAttestationFactory,
)

TEXT = TextFactory.build()
CHAPTER = ChapterFactory.build(text_id=TEXT.id)
MANUSCRIPT_ATTESTATION = ManuscriptAttestationFactory.create(
    text=attr.evolve(TEXT, references=()),
    chapter_id=CHAPTER.id_,
    manuscript=CHAPTER.manuscripts[0],
)


@pytest.mark.parametrize(
    "manuscript_attestation,expected",
    [
        (
            ManuscriptAttestation(
                attr.evolve(TEXT, references=()), CHAPTER.id_, CHAPTER.manuscripts[0]
            ),
            MANUSCRIPT_ATTESTATION,
        ),
    ],
)
def test_manuscript_attestation(manuscript_attestation, expected) -> None:
    assert manuscript_attestation == expected
