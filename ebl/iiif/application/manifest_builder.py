from typing import Optional, Sequence

import attr

from ebl.iiif.application.canvas_builder import CanvasBuilder
from ebl.iiif.application.iiif_identifiers import IiifIdentifierFactory
from ebl.iiif.application.image_service import ImageServiceLocator
from ebl.iiif.application.manifest_sources import (
    FragmentSource,
    MediaSource,
    MetadataSource,
)
from ebl.iiif.application.publication import IiifPublicationPolicy
from ebl.iiif.domain.canvas import Canvas
from ebl.iiif.domain.language_map import LanguageMap
from ebl.iiif.domain.manifest import Manifest
from ebl.iiif.domain.resources import (
    Agent,
    ExternalResource,
    ImageResource,
    MetadataEntry,
    RequiredStatement,
)

ATTRIBUTION_LABEL = "Attribution"
HOMEPAGE_TYPE = "Text"
HOMEPAGE_FORMAT = "text/html"
RECORD_TYPE = "Dataset"
RECORD_FORMAT = "application/json"


@attr.attrs(auto_attribs=True, frozen=True)
class ManifestProvider:
    id: str
    label: str


class ManifestBuilder:
    def __init__(
        self,
        identifiers: IiifIdentifierFactory,
        image_services: ImageServiceLocator,
        provider: Optional[ManifestProvider] = None,
        policy: Optional[IiifPublicationPolicy] = None,
    ):
        self._identifiers = identifiers
        self._policy = policy or IiifPublicationPolicy()
        self._canvases = CanvasBuilder(identifiers, image_services)
        self._provider = provider

    def build(self, fragment: FragmentSource) -> Optional[Manifest]:
        media = self._policy.publishable_media(fragment)
        if not media or not self._policy.has_uniform_terms(media):
            return None
        canvases = [self._canvases.build(fragment.number, item) for item in media]
        return Manifest(
            id=self._identifiers.manifest(fragment.number),
            label=LanguageMap.of(str(fragment.number)),
            items=canvases,
            summary=LanguageMap.optional(fragment.summary, "en"),
            metadata=self._metadata(fragment.metadata),
            required_statement=self._required_statement(media),
            rights=self._policy.common_rights(media),
            provider=self._providers(),
            homepage=self._homepage(fragment),
            see_also=self._see_also(fragment),
            thumbnail=self._thumbnail(canvases, media),
        )

    @staticmethod
    def _metadata(metadata: Sequence[MetadataSource]) -> Sequence[MetadataEntry]:
        return [
            MetadataEntry(
                label=LanguageMap.of(entry.label, "en"),
                value=LanguageMap.of(entry.value),
            )
            for entry in metadata
        ]

    def _required_statement(
        self, media: Sequence[MediaSource]
    ) -> Optional[RequiredStatement]:
        attribution = self._policy.common_attribution(media)
        return (
            None
            if attribution is None
            else RequiredStatement(
                label=LanguageMap.of(ATTRIBUTION_LABEL, "en"),
                value=LanguageMap.of(attribution, "en"),
            )
        )

    def _providers(self) -> Sequence[Agent]:
        provider = self._provider
        return (
            ()
            if provider is None
            else [Agent(id=provider.id, label=LanguageMap.of(provider.label, "en"))]
        )

    @staticmethod
    def _homepage(fragment: FragmentSource) -> Sequence[ExternalResource]:
        return (
            ()
            if fragment.homepage_url is None
            else [
                ExternalResource(
                    id=fragment.homepage_url,
                    type=HOMEPAGE_TYPE,
                    label=LanguageMap.of(str(fragment.number)),
                    format=HOMEPAGE_FORMAT,
                )
            ]
        )

    @staticmethod
    def _see_also(fragment: FragmentSource) -> Sequence[ExternalResource]:
        return (
            ()
            if fragment.record_url is None
            else [
                ExternalResource(
                    id=fragment.record_url,
                    type=RECORD_TYPE,
                    label=LanguageMap.of("eBL fragment record", "en"),
                    format=RECORD_FORMAT,
                )
            ]
        )

    @staticmethod
    def _thumbnail(
        canvases: Sequence[Canvas], media: Sequence[MediaSource]
    ) -> Sequence[ImageResource]:
        primary = next(
            (index for index, item in enumerate(media) if item.is_primary), 0
        )
        return canvases[primary].thumbnail
