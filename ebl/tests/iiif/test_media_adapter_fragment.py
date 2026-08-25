from ebl.common.domain.project import ResearchProject
from ebl.common.domain.scopes import Scope
from ebl.iiif.application.manifest_sources import MetadataSource
from ebl.iiif.application.media_adapter import (
    PROJECT_LABEL,
    REFERENCE_LABEL,
    fragment_source_of,
    media_metadata_of,
)
from ebl.tests.media.factories import (
    DEFAULT_COPY_MEDIA_ID,
    DEFAULT_MEDIA_ID,
    association,
    copy_media,
    media_reference,
    photo_media,
)
from ebl.transliteration.domain.museum_number import MuseumNumber

NUMBER = MuseumNumber.of("K.1")
OTHER_NUMBER = MuseumNumber.of("K.2")


def test_metadata_is_empty_without_projects_or_references() -> None:
    assert media_metadata_of((photo_media(),)) == ()


def test_metadata_maps_projects_and_references() -> None:
    media = photo_media(
        projects=(ResearchProject.CAIC,),
        references=(media_reference("bibliography-1"),),
    )

    assert media_metadata_of((media,)) == (
        MetadataSource(label=PROJECT_LABEL, value=ResearchProject.CAIC.long_name),
        MetadataSource(label=REFERENCE_LABEL, value="bibliography-1"),
    )


def test_metadata_deduplicates_across_media_preserving_order() -> None:
    first = photo_media(
        projects=(ResearchProject.CAIC, ResearchProject.AMPS),
        references=(media_reference("bibliography-1"),),
    )
    second = copy_media(
        projects=(ResearchProject.CAIC,),
        references=(media_reference("bibliography-1"), media_reference("b-2")),
    )

    assert media_metadata_of((first, second)) == (
        MetadataSource(label=PROJECT_LABEL, value=ResearchProject.CAIC.long_name),
        MetadataSource(label=PROJECT_LABEL, value=ResearchProject.AMPS.long_name),
        MetadataSource(label=REFERENCE_LABEL, value="bibliography-1"),
        MetadataSource(label=REFERENCE_LABEL, value="b-2"),
    )


def test_fragment_source_maps_number_and_associated_media() -> None:
    source = fragment_source_of(NUMBER, (photo_media(),))

    assert source.number == NUMBER
    assert [media.media_id for media in source.media] == [DEFAULT_MEDIA_ID]


def test_fragment_source_skips_media_associated_with_other_fragments() -> None:
    associated = photo_media()
    unassociated = copy_media(
        associations=(association(fragment_id="K.99", is_primary=False),)
    )

    source = fragment_source_of(NUMBER, (associated, unassociated))

    assert [media.media_id for media in source.media] == [DEFAULT_MEDIA_ID]


def test_fragment_source_keeps_media_associated_with_several_fragments() -> None:
    shared = copy_media(
        associations=(
            association(fragment_id="K.1", sort_order=1, is_primary=False),
            association(fragment_id="K.2", sort_order=0, is_primary=True),
        )
    )

    source = fragment_source_of(NUMBER, (shared,))

    assert [media.media_id for media in source.media] == [DEFAULT_COPY_MEDIA_ID]
    assert source.media[0].sort_order == 1
    assert source.media[0].is_primary is False


def test_fragment_source_carries_authorized_scopes() -> None:
    source = fragment_source_of(
        NUMBER, (photo_media(),), authorized_scopes=(Scope.READ_CAIC_FRAGMENTS,)
    )

    assert source.authorized_scopes == (Scope.READ_CAIC_FRAGMENTS,)


def test_fragment_source_defaults_to_no_scopes_and_no_links() -> None:
    source = fragment_source_of(NUMBER, ())

    assert source.authorized_scopes == ()
    assert source.media == ()
    assert source.metadata == ()
    assert source.summary is None
    assert source.homepage_url is None
    assert source.record_url is None


def test_fragment_source_carries_summary_and_links() -> None:
    source = fragment_source_of(
        NUMBER,
        (photo_media(),),
        summary="A fragment.",
        homepage_url="https://www.ebl.lmu.de/fragmentarium/K.1",
        record_url="https://api.ebl.lmu.de/fragments/K.1",
    )

    assert source.summary == "A fragment."
    assert source.homepage_url == "https://www.ebl.lmu.de/fragmentarium/K.1"
    assert source.record_url == "https://api.ebl.lmu.de/fragments/K.1"
