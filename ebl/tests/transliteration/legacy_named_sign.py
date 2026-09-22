"""The legacy interleaved named-sign shape, shared by the migration tests."""

from typing import Any, Dict

LEGACY_PART = {"value": "k", "type": "ValueToken"}
LEGACY_BREAK = {"value": "]", "type": "BrokenAway", "side": "RIGHT"}
LEGACY_TAIL = {"value": "u", "type": "ValueToken"}


def legacy_fragment() -> Dict[str, Any]:
    return {
        "text": {
            "lines": [
                {
                    "content": [
                        {
                            "parts": [
                                {"nameParts": [LEGACY_PART, LEGACY_BREAK, LEGACY_TAIL]}
                            ]
                        }
                    ]
                }
            ]
        }
    }


def named_sign(document: Dict[str, Any]) -> Dict[str, Any]:
    return document["text"]["lines"][0]["content"][0]["parts"][0]
