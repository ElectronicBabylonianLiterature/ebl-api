import time
from typing import Optional, cast

import falcon
from falcon.testing import Result
from pymongo.errors import PyMongoError

from ebl.fragmentarium.domain.fragment import Notes, Introduction
from ebl.transliteration.domain.markup import StringPart, EmphasisPart


NOTES_FIXTURE = [
    [Notes(), Notes("Some notes", (StringPart("Some notes"),))],
    [Notes(), Notes()],
    [Notes("Different notes"), Notes()],
    [
        Notes("Different notes"),
        Notes(
            "Different notes @i{with emphasis}",
            (StringPart("Different notes "), EmphasisPart("with emphasis")),
        ),
    ],
]

INTRO_FIXTURE = [
    [
        Introduction(),
        Introduction(
            "A new introduction",
            (StringPart("A new introduction"),),
        ),
    ],
    [
        Introduction(
            "An old introduction",
            (StringPart("An old introduction"),),
        ),
        Introduction(),
    ],
    [
        Introduction(),
        Introduction(),
    ],
]


def simulate_post_with_retry(client, url, body) -> Result:
    result: Optional[Result] = None
    for attempt in range(3):
        result = cast(Result, client.simulate_post(url, body=body))
        if result.status != falcon.HTTP_INTERNAL_SERVER_ERROR:
            return result

        payload = ""
        try:
            payload = str(result.json)
        except Exception:
            payload = result.text or ""

        if "operation cancelled" not in payload.lower() or attempt == 2:
            return result
        time.sleep(0.1)

    assert result is not None
    return result


def find_changelog_entry(database, query):
    for attempt in range(3):
        try:
            return database["changelog"].find_one(query)
        except PyMongoError as error:
            if "operation cancelled" not in str(error).lower() or attempt == 2:
                raise
            time.sleep(0.1)
    return None
