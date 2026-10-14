import hashlib

import attr

from ebl.media.domain import MediaChecksum, MediaRepresentation


def representation_for_content(
    content: bytes, representation: MediaRepresentation
) -> MediaRepresentation:
    checksum = (
        MediaChecksum(value=hashlib.sha256(content).hexdigest())
        if representation.checksum is not None
        else None
    )
    return attr.evolve(representation, file_size=len(content), checksum=checksum)
