import falcon

from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.factories.corpus import (
    TextFactory,
    ChapterFactory,
    ManuscriptFactory,
    ManuscriptAttestationFactory,
    UncertainFragmentAttestationFactory,
)
from ebl.corpus.application.schemas import (
    ManuscriptAttestationSchema,
    UncertainFragmentAttestationSchema,
)

MUSEUM_NUMBER_MANUSCRIPT = MuseumNumber("X", "1")
FRAGMENT_MANUSCRIPT = FragmentFactory.build(number=MUSEUM_NUMBER_MANUSCRIPT)
MUSEUM_NUMBER_UNCERTAIN = MuseumNumber("X", "500")
FRAGMENT_UNCERTAIN = FragmentFactory.build(number=MUSEUM_NUMBER_UNCERTAIN)

TEXT = TextFactory.build()
CHAPTER = ChapterFactory.build(
    text_id=TEXT.id,
    stage=TEXT.chapters[0].stage,
    name=TEXT.chapters[0].name,
    manuscripts=(
        ManuscriptFactory.build(
            id=1,
            museum_number=MUSEUM_NUMBER_MANUSCRIPT,
            accession="",
            references=(),
        ),
    ),
    uncertain_fragments=[MUSEUM_NUMBER_UNCERTAIN],
)

MANUSCRIPT_ATTESTATION = ManuscriptAttestationFactory.build(
    text=TEXT,
    chapter_id=CHAPTER.id_,
    manuscript=CHAPTER.manuscripts[0],
)

UNCERTAIN_FRAGMENT_ATTESTATION = UncertainFragmentAttestationFactory.build(
    text=TEXT,
    chapter_id=CHAPTER.id_,
)


def test_search_fragment_attestations_in_corpus_as_manuscript(
    client, fragmentarium, text_repository
):
    fragmentarium.create(FRAGMENT_MANUSCRIPT)
    text_repository.create(TEXT)
    text_repository.create_chapter(CHAPTER)
    result = client.simulate_get("/fragments/X.1/corpus")
    assert result.status == falcon.HTTP_OK
    assert result.headers["Content-Type"] == "application/json"
    assert result.json == {
        "manuscriptAttestations": [
            ManuscriptAttestationSchema().dump(MANUSCRIPT_ATTESTATION)
        ],
        "uncertainFragmentAttestations": [],
    }


def test_search_fragment_attestations_in_corpus_as_uncertain(
    client, fragmentarium, text_repository
):
    fragmentarium.create(FRAGMENT_UNCERTAIN)
    text_repository.create(TEXT)
    text_repository.create_chapter(CHAPTER)
    result = client.simulate_get("/fragments/X.500/corpus")
    assert result.status == falcon.HTTP_OK
    assert result.headers["Content-Type"] == "application/json"
    assert result.json == {
        "manuscriptAttestations": [],
        "uncertainFragmentAttestations": [
            UncertainFragmentAttestationSchema().dump(UNCERTAIN_FRAGMENT_ATTESTATION)
        ],
    }
