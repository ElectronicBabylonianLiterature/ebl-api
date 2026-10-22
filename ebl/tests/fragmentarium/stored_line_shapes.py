from typing import Any, Dict

SPARSE_DEFAULTS: Dict[str, Any] = {"erasure": "NONE", "enclosureType": []}
STORAGE_DEFAULTS: Dict[str, Any] = {"erasure": "NONE", "nameBreaks": []}


def sparse_shape(value: Any, defaults: Dict[str, Any] = SPARSE_DEFAULTS) -> Any:
    if isinstance(value, list):
        return [sparse_shape(item, defaults) for item in value]
    if isinstance(value, dict):
        return {
            key: sparse_shape(item, defaults)
            for key, item in value.items()
            if defaults.get(key, object()) != item
        }
    return value


def interleaved(parts: list, breaks: list) -> list:
    merged = []
    for index, part in enumerate(parts):
        merged.append(part)
        if index < len(breaks):
            merged.append(breaks[index])
    return merged


def legacy_shape(value: Any) -> Any:
    if isinstance(value, list):
        return [legacy_shape(item) for item in value]
    if not isinstance(value, dict):
        return value
    converted = {key: legacy_shape(item) for key, item in value.items()}
    if "nameBreaks" not in converted:
        return converted
    breaks = converted.pop("nameBreaks")
    return {**converted, "nameParts": interleaved(converted["nameParts"], breaks)}
