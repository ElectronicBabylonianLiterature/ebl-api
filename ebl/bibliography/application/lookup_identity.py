from typing import Mapping


def bibliography_lookup_values(entry: Mapping) -> list[str]:
    values = [entry["id"]]
    if isinstance(citation_key := entry.get("citationKey"), str) and citation_key:
        values.append(citation_key)
    for alias in entry.get("aliases", []):
        if not isinstance(alias, Mapping):
            continue
        values.extend(
            value
            for value in (alias.get("value"), alias.get("normalizedValue"))
            if isinstance(value, str) and value
        )
    return values
