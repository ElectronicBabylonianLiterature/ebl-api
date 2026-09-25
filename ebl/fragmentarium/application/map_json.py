from __future__ import annotations

import json


def load_strict_json(content: str, context: str) -> object:
    def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key {key!r} in {context}.")
            result[key] = value
        return result

    def reject_nonfinite(value: str) -> None:
        raise ValueError(f"Non-finite JSON value {value!r} in {context}.")

    return json.loads(
        content,
        object_pairs_hook=reject_duplicate_keys,
        parse_constant=reject_nonfinite,
    )
