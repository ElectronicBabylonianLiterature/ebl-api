from typing import Any, Dict, cast

from ebl.transliteration.application.text_schema import TextSchema

TRANSLITERATION_FIELDS = ("colophon", "unplacedLines")


def api_transliteration_of(stored_transliteration: dict) -> Dict[str, Any]:
    schema = TextSchema()
    return cast(Dict[str, Any], schema.dump(schema.load(stored_transliteration)))


def api_manuscript_of(stored_manuscript: dict) -> Dict[str, Any]:
    return {
        **stored_manuscript,
        **{
            key: api_transliteration_of(stored_manuscript[key])
            for key in TRANSLITERATION_FIELDS
            if key in stored_manuscript
        },
    }


def api_sign_data_of(stored_chapter: dict) -> Dict[str, Any]:
    return {
        **stored_chapter,
        "manuscripts": [
            api_manuscript_of(manuscript)
            for manuscript in stored_chapter["manuscripts"]
        ],
    }
