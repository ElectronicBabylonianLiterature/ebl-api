import hashlib
import io
from contextlib import ExitStack
from operator import attrgetter
from typing import BinaryIO, cast

from PIL import Image

from ebl.media.domain import MediaChecksum, MediaRepresentation
from ebl.media.infrastructure.prepared_upload import UploadContent

LANCZOS_RESAMPLING = attrgetter("LANCZOS")(Image)

HIGH_BIT_DEPTH_MODES = frozenset({"I", "I;16", "I;16L", "I;16B", "F"})


def eight_bit(image: Image.Image) -> Image.Image:
    """Rescale high-bit-depth grayscale to 8-bit "L", closing the input if converted.

    16-bit PNG greyscale decodes to "I;16"; a plain ``convert`` clips every
    value above 255 to white, and LANCZOS resizing rejects the mode. Samples are
    scaled over the full 16-bit range (value / 256, i.e. the high byte), not
    stretched per image, so preview tones match the original's encoded values.
    16-bit colour and grey+alpha PNGs already decode to 8-bit "RGB"/"RGBA".
    """
    if image.mode not in HIGH_BIT_DEPTH_MODES:
        return image
    with image:
        if image.mode == "I;16":
            # Stays two bytes per pixel; Pillow applies a 65536-entry lookup.
            scaled = image.point(lambda value: value * (1 / 256))
        else:
            with image.convert("F") as floating:
                scaled = floating.point(lambda value: value * (1 / 256))
        with scaled:
            # Out-of-range "I"/"F" samples are clamped to 0..255 here.
            return scaled.convert("L")


def preview(source: Image.Image, pixels: int, stack: ExitStack) -> UploadContent:
    with source.copy() as image:
        image.thumbnail((pixels, pixels), LANCZOS_RESAMPLING)
        # Flatten transparent copies onto white, rather than replacing ink with black.
        if image.mode in {"RGBA", "LA"} or (
            image.mode == "P" and "transparency" in image.info
        ):
            with image.convert("RGBA") as rgba:
                with Image.new("RGB", image.size, "white") as rgb:
                    rgb.paste(rgba, mask=rgba.getchannel("A"))
                    output = stack.enter_context(io.BytesIO())
                    rgb.save(output, format="JPEG", quality=85, optimize=True)
        else:
            with image.convert("RGB") as rgb:
                output = stack.enter_context(io.BytesIO())
                rgb.save(output, format="JPEG", quality=85, optimize=True)
        value = output.getvalue()
        output.seek(0)
        return UploadContent(
            MediaRepresentation(
                "image/jpeg",
                image.width,
                image.height,
                len(value),
                MediaChecksum(value=hashlib.sha256(value).hexdigest()),
            ),
            cast(BinaryIO, output),
        )
