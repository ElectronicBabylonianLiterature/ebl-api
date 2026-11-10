from io import BytesIO

from PIL import Image, features


def verify_pillow_codecs() -> None:
    assert features.check_codec("jpg"), "Pillow must provide JPEG support"
    assert features.check_codec("zlib"), "Pillow must provide PNG support"
    assert features.check("webp"), "Pillow must provide WebP support"
    for image_format in ("JPEG", "PNG", "WEBP"):
        with BytesIO() as content:
            with Image.new("RGB", (16, 12)) as original:
                original.save(content, format=image_format)
            content.seek(0)
            with Image.open(content) as image:
                image.load()
                assert image.format == image_format
                image.thumbnail((8, 8))
                assert image.size == (8, 6)
                image.save(BytesIO(), format=image_format)
        print(f"{image_format}: encode, decode and thumbnail passed")


if __name__ == "__main__":
    verify_pillow_codecs()
