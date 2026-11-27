"""Recode the digital MesZL (Kapitel III, ``signs.mesZl``) for Borger's font.

Borger Akkadian 0.9.12 gives several of Borger's own drawings their own
private-use code points. Where the digital MesZL approximated those forms
with other signs (or with CSS), the text is recoded here. Each recoding names
the signs whose text contains it and an exact passage, so that only that
occurrence changes; a passage that is missing (or already recoded) is reported
and left alone.

Usage::

    MONGODB_URI=… MONGODB_DB=… python -m ebl.signs.recode_mes_zl --dry-run
    MONGODB_URI=… MONGODB_DB=… python -m ebl.signs.recode_mes_zl
"""

import argparse
import logging
import os
import sys
from typing import Iterable, Optional, Sequence

import attr
from pymongo import MongoClient

from ebl.signs.infrastructure.sign_schemas import COLLECTION

logger = logging.getLogger(__name__)

ROTATED_GIR3 = (
    '𒄊<span style="display:inline-block; transform:rotate(180deg); '
    "-webkit-transform: rotate(180deg); -moz-transform: rotate(180deg); "
    '-o-transform: rotate(180deg);">𒄊</span>'
)


@attr.s(auto_attribs=True, frozen=True)
class Recoding:
    mes_zl: str
    signs: Sequence[str]
    old: str
    new: str
    note: str


RECODINGS: Sequence[Recoding] = (
    Recoding(
        "114a",
        ("EŠE₃",),
        "𒀸𒐴 (AŠ+Ugunû)",
        "\U001000c3 (AŠ+Ugunû)",
        "AŠ+Ugunû as Borger's single sign 114a (U+1000C3), as in Kapitel II.",
    ),
    Recoding(
        "144v",
        ("NUN@t",),
        "𒉩 und \U00100043 siehe Kap. II.",
        "𒉩 und \U001000cc siehe Kap. II.",
        "Neo-Babylonian NUN-tenû 144v (U+1000CC) instead of NUN variant 143v.",
    ),
    Recoding(
        "298v",
        ("DUH", "GABA"),
        "Zur Differenzierung von 𒂃 und \U00100067",
        "Zur Differenzierung von \U001000c5 und \U00100067",
        "Neo-Babylonian DUH 298v (U+1000C5), as in Kapitel II.",
    ),
    Recoding(
        "701c",
        ("GIR₃", "PIRIG"),
        f"{ROTATED_GIR3} siehe Kap. II.",
        "\U001000c8 siehe Kap. II.",
        "GÌR + GÌR inversum 701c (U+1000C8) instead of a CSS-rotated GÌR.",
    ),
    Recoding(
        "94",
        ("|PAP.PAP|",),
        "𒊺𒊺\U00100018 usw. = ŠE-MUNU₇",
        "𒊺\U00100018 usw. = ŠE-MUNU₇",
        "U+100018 already contains a ŠE.",
    ),
)


@attr.s(auto_attribs=True, frozen=True)
class RecodingResult:
    recoding: Recoding
    sign: str
    status: str  # "recoded", "already recoded", "passage not found", "no sign"


def recode_text(text: str, recoding: Recoding) -> Optional[str]:
    """The recoded text, or None when the passage is not there exactly once."""
    if text.count(recoding.old) != 1:
        return None
    return text.replace(recoding.old, recoding.new)


def _status(text: Optional[str], recoding: Recoding) -> tuple[str, Optional[str]]:
    if text is None:
        return "no sign", None
    recoded = recode_text(text, recoding)
    if recoded is not None:
        return "recoded", recoded
    if recoding.new in text:
        return "already recoded", None
    return "passage not found", None


def run_recoding(
    collection, recodings: Iterable[Recoding] = RECODINGS, dry_run: bool = False
) -> list[RecodingResult]:
    results = []
    for recoding in recodings:
        for sign in recoding.signs:
            document = collection.find_one({"_id": sign}, {"mesZl": 1})
            text = None if document is None else document.get("mesZl") or ""
            status, recoded = _status(text, recoding)
            if recoded is not None and not dry_run:
                collection.update_one({"_id": sign}, {"$set": {"mesZl": recoded}})
            results.append(RecodingResult(recoding, sign, status))
    return results


def get_database():
    client = MongoClient(os.environ["MONGODB_URI"])
    return client.get_database(os.environ.get("MONGODB_DB"))


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dry-run", action="store_true")
    arguments = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    results = run_recoding(get_database()[COLLECTION], dry_run=arguments.dry_run)
    for result in results:
        logger.info(
            "MesZL %s, %s: %s%s",
            result.recoding.mes_zl,
            result.sign,
            result.status,
            " (dry run)" if arguments.dry_run and result.status == "recoded" else "",
        )
    failed = [
        result
        for result in results
        if result.status in ("passage not found", "no sign")
    ]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
