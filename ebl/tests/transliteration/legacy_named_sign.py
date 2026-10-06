from typing import Any, Dict

LEGACY_PART = {"value": "k", "type": "ValueToken"}
LEGACY_BREAK = {"value": "]", "type": "BrokenAway", "side": "RIGHT"}
LEGACY_TAIL = {"value": "u", "type": "ValueToken"}
NAMED_SIGN_PATH = "text.lines.0.content.0.parts.0"
LATER_NAMED_SIGN_PATH = "text.lines.1.content.1.parts.1"


def legacy_name() -> Dict[str, Any]:
    return {"nameParts": [LEGACY_PART, LEGACY_BREAK, LEGACY_TAIL]}


def legacy_fragment() -> Dict[str, Any]:
    return {"text": {"lines": [{"content": [{"parts": [legacy_name()]}]}]}}


def legacy_fragment_with_a_later_name() -> Dict[str, Any]:
    later_content = {"parts": [{"value": "x"}, legacy_name()]}
    return {
        "text": {
            "lines": [
                {"content": []},
                {"content": [{"parts": []}, later_content]},
            ]
        }
    }


def named_sign(document: Dict[str, Any]) -> Dict[str, Any]:
    return document["text"]["lines"][0]["content"][0]["parts"][0]


def later_named_sign(document: Dict[str, Any]) -> Dict[str, Any]:
    return document["text"]["lines"][1]["content"][1]["parts"][1]
