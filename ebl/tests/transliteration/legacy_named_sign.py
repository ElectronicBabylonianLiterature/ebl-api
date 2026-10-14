from collections.abc import Mapping

from pymongo.collection import Collection

MODULE = "ebl.transliteration.migrate_name_breaks"
LEGACY_PART = {"value": "k", "type": "ValueToken"}
LEGACY_BREAK = {"value": "]", "type": "BrokenAway", "side": "RIGHT"}
LEGACY_TAIL = {"value": "u", "type": "ValueToken"}
NAMED_SIGN_PATH = "text.lines.0.content.0.parts.0"
LATER_NAMED_SIGN_PATH = "text.lines.1.content.1.parts.1"


def legacy_name() -> dict[str, object]:
    return {"nameParts": [LEGACY_PART, LEGACY_BREAK, LEGACY_TAIL]}


def legacy_fragment() -> dict[str, object]:
    return {"text": {"lines": [{"content": [{"parts": [legacy_name()]}]}]}}


def legacy_fragment_with_a_later_name() -> dict[str, object]:
    later_content = {"parts": [{"value": "x"}, legacy_name()]}
    return {
        "text": {
            "lines": [
                {"content": []},
                {"content": [{"parts": []}, later_content]},
            ]
        }
    }


def value_at(document: object, path: str) -> object:
    value = document
    for key in path.split("."):
        assert isinstance(value, (list, Mapping))
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def mapping_at(document: object, path: str) -> Mapping[str, object]:
    value = value_at(document, path)
    assert isinstance(value, Mapping)
    return value


def named_sign(document: object) -> Mapping[str, object]:
    return mapping_at(document, NAMED_SIGN_PATH)


def later_named_sign(document: object) -> Mapping[str, object]:
    return mapping_at(document, LATER_NAMED_SIGN_PATH)


def stored_document(collection: Collection, document_id: str) -> Mapping[str, object]:
    document = collection.find_one({"_id": document_id})
    assert document is not None
    return document
