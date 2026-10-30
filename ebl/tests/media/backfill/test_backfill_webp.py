import io
from collections.abc import Callable
from typing import NoReturn

import pytest
from PIL import Image
from pymongo.database import Database

from ebl.media.application.backfill_plan import BackfillPolicy, SourceRejected
from ebl.media.application.media_requests import BackfillRequest
from ebl.media.infrastructure.backfill_images import inspect_image


def webp_content(*, lossless: bool = False, animated: bool = False) -> bytes:
    with Image.new("RGB", (16, 12), "red") as first:
        with Image.new("RGB", (16, 12), "blue") as second:
            output = io.BytesIO()
            first.save(
                output,
                format="WEBP",
                lossless=lossless,
                save_all=animated,
                append_images=[second] if animated else [],
            )
            return output.getvalue()


def reject_decoder(*arguments: object, **options: object) -> NoReturn:
    raise AssertionError("Native decoder must not be constructed.")


@pytest.mark.parametrize("lossless", [False, True], ids=["lossy", "lossless"])
def test_valid_webp_at_policy_boundary(lossless: bool) -> None:
    content = webp_content(lossless=lossless)
    representation, evidence = inspect_image(
        io.BytesIO(content), len(content), BackfillPolicy(max_pixels=192)
    )
    assert (representation.mime_type, representation.width, representation.height) == (
        "image/webp",
        16,
        12,
    )
    assert evidence == {}


@pytest.mark.parametrize("lossless", [False, True], ids=["lossy", "lossless"])
def test_webp_policy_limit_precedes_decoder(
    lossless: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    content = webp_content(lossless=lossless)
    monkeypatch.setattr(Image, "open", reject_decoder)
    with pytest.raises(SourceRejected) as rejected:
        inspect_image(io.BytesIO(content), len(content), BackfillPolicy(max_pixels=191))
    assert (rejected.value.outcome, rejected.value.reason) == (
        "review",
        "pixel-inspection-limit",
    )


@pytest.mark.parametrize(
    "generate_previews", [False, True], ids=["original", "previews"]
)
def test_oversized_webp_plan_never_constructs_decoder(
    database: Database,
    legacy_photo: Callable,
    migration_factory: Callable,
    monkeypatch: pytest.MonkeyPatch,
    generate_previews: bool,
) -> None:
    content = bytearray(webp_content(animated=True))
    assert content[12:16] == b"VP8X"
    content[24:27] = (9999).to_bytes(3, "little")
    content[27:30] = (9999).to_bytes(3, "little")
    legacy_photo(filename="K.1.webp", content=bytes(content))
    before = {
        name: list(database[name].find()) for name in database.list_collection_names()
    }
    migration = migration_factory(
        BackfillPolicy(generate_previews=generate_previews), initialize=False
    )
    monkeypatch.setattr(Image, "open", reject_decoder)
    planned = tuple(migration.plan_batch(BackfillRequest()))
    assert len(planned) == 1
    assert (planned[0].outcome, planned[0].reason) == (
        "review",
        "pixel-inspection-limit",
    )
    assert {
        name: list(database[name].find()) for name in database.list_collection_names()
    } == before


def test_malformed_webp_rejects_before_decoder(monkeypatch: pytest.MonkeyPatch) -> None:
    content = b"RIFF\x16\x00\x00\x00WEBPVP8X"
    monkeypatch.setattr(Image, "open", reject_decoder)
    with pytest.raises(SourceRejected) as rejected:
        inspect_image(io.BytesIO(content), len(content), BackfillPolicy())
    assert (rejected.value.outcome, rejected.value.reason) == (
        "blocked",
        "malformed-original",
    )
