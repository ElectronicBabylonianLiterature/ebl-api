from io import BytesIO

from PIL import Image, features


def verify_pillow_codecs() -> None:
    if not features.check_codec("jpg"):
        raise SystemExit("Pillow must provide JPEG support")
    if not features.check_codec("zlib"):
        raise SystemExit("Pillow must provide PNG support")
    if not features.check("webp"):
        raise SystemExit("Pillow must provide WebP support")
    for image_format in ("JPEG", "PNG", "WEBP"):
        with BytesIO() as content:
            with Image.new("RGB", (16, 12)) as original:
                original.save(content, format=image_format)
            content.seek(0)
            with Image.open(content) as image:
                image.load()
                if image.format != image_format:
                    raise SystemExit(f"Pillow must preserve {image_format} format")
                image.thumbnail((8, 8))
                if image.size != (8, 6):
                    raise SystemExit(f"Pillow must thumbnail {image_format} to 8x6")
                image.save(BytesIO(), format=image_format)
        print(f"{image_format}: encode, decode and thumbnail passed")


if __name__ == "__main__":
    verify_pillow_codecs()
