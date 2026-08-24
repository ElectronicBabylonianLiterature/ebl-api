from urllib.parse import quote, urlparse

from ebl.iiif.application.fragment_identity import FragmentIiifIdentity
from ebl.transliteration.domain.museum_number import MuseumNumber

IIIF_NAMESPACE = "iiif/3"
ALLOWED_SCHEMES = ("http", "https")


def normalize_base_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise ValueError(f"IIIF base URL must be http or https, got {base_url!r}.")
    if not parsed.netloc:
        raise ValueError(f"IIIF base URL must include a host, got {base_url!r}.")
    if parsed.query or parsed.fragment:
        raise ValueError(
            f"IIIF base URL must not carry a query or fragment, got {base_url!r}."
        )
    return base_url.rstrip("/")


class IiifIdentifierFactory:
    def __init__(self, base_url: str, fragment_identity: FragmentIiifIdentity):
        self._base_url = normalize_base_url(base_url)
        self._fragment_identity = fragment_identity

    @property
    def fragment_identity(self) -> FragmentIiifIdentity:
        return self._fragment_identity

    def manifest(self, number: MuseumNumber) -> str:
        return f"{self._fragment_base(number)}/manifest"

    def canvas(self, number: MuseumNumber, media_id: str) -> str:
        return f"{self._fragment_base(number)}/canvas/{self._media_segment(media_id)}"

    def painting_page(self, number: MuseumNumber, media_id: str) -> str:
        return f"{self.canvas(number, media_id)}/page/painting"

    def painting_annotation(self, number: MuseumNumber, media_id: str) -> str:
        return f"{self.canvas(number, media_id)}/annotation/painting"

    def absolute(self, path: str) -> str:
        return f"{self._base_url}/{path.lstrip('/')}"

    def _fragment_base(self, number: MuseumNumber) -> str:
        identifier = self._fragment_identity.identifier_of(number)
        return f"{self._base_url}/{IIIF_NAMESPACE}/fragment/{identifier}"

    @staticmethod
    def _media_segment(media_id: str) -> str:
        if not media_id:
            raise ValueError("A IIIF media identifier must not be empty.")
        return quote(media_id, safe="")
