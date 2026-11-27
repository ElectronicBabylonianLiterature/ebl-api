"""Import Borger, MesZL² Kapitel II into the ``meszl_kap2`` collection.

The input is a JSON object keyed by MesZL number; each value is the entry text
(``"<number>\\t<sign>\\t**— NAME — …**\\n…"``). The introduction is stored under
the key ``_Einleitung``. Existing entries are replaced.

Usage::

    MONGODB_URI=… MONGODB_DB=… python -m ebl.signs.import_mes_zl_kap2 MesZL_Kap_II.json
    python -m ebl.signs.import_mes_zl_kap2 MesZL_Kap_II.json --dry-run
"""

import argparse
import json
import logging
import os
import sys
from typing import Iterable, Mapping, Sequence

from pymongo import MongoClient

from ebl.signs.application.mes_zl_kap2_repository import mes_zl_number_variants
from ebl.signs.infrastructure.mongo_mes_zl_kap2_repository import (
    MongoMesZlKap2Repository,
)
from ebl.signs.infrastructure.sign_schemas import COLLECTION as SIGNS_COLLECTION

logger = logging.getLogger(__name__)

INTRODUCTION_KEY = "_Einleitung"


def load_entries(path: str) -> dict[str, str]:
    with open(path, encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object keyed by MesZL number.")
    entries = {}
    for key, value in data.items():
        if not isinstance(value, str):
            raise ValueError(f"Entry {key!r} is not a string.")
        entries[str(key).strip()] = value
    return entries


def unmatched_numbers(
    entries: Iterable[str], sign_numbers: Iterable[str]
) -> Sequence[str]:
    known = {
        variant for number in sign_numbers for variant in mes_zl_number_variants(number)
    }
    return [
        number
        for number in entries
        if number != INTRODUCTION_KEY and number not in known
    ]


def mes_zl_numbers_of_signs(database) -> list[str]:
    return [
        record["number"]
        for sign in database[SIGNS_COLLECTION].find({"lists.name": "MZL"}, {"lists": 1})
        for record in sign.get("lists", [])
        if record.get("name") == "MZL"
    ]


def run_import(database, entries: Mapping[str, str], dry_run: bool = False) -> dict:
    unmatched = unmatched_numbers(entries, mes_zl_numbers_of_signs(database))
    imported = 0 if dry_run else MongoMesZlKap2Repository(database).replace_all(entries)
    return {
        "entries": len(entries),
        "imported": imported,
        "unmatched": list(unmatched),
        "dry_run": dry_run,
    }


def get_database():
    client = MongoClient(os.environ["MONGODB_URI"])
    return client.get_database(os.environ.get("MONGODB_DB"))


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("path", help="JSON file keyed by MesZL number")
    parser.add_argument("--dry-run", action="store_true")
    arguments = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    report = run_import(get_database(), load_entries(arguments.path), arguments.dry_run)
    logger.info(
        "%s entries read, %s imported%s.",
        report["entries"],
        report["imported"],
        " (dry run)" if report["dry_run"] else "",
    )
    if report["unmatched"]:
        logger.info(
            "%s entries have no sign with that MesZL number: %s",
            len(report["unmatched"]),
            ", ".join(report["unmatched"]),
        )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
