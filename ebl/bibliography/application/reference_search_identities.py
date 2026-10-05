from typing import Callable, Iterable, Mapping, Tuple

import attr


def _unique(values: Iterable[str]) -> Tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _strings(values: Iterable[object]) -> Tuple[str, ...]:
    return _unique(value for value in values if isinstance(value, str) and value)


@attr.s(auto_attribs=True, frozen=True)
class ReferenceSearchIdentities:
    bibliography_ids: Tuple[str, ...] = ()
    citation_keys: Tuple[str, ...] = ()
    alias_values: Tuple[str, ...] = ()
    normalized_alias_values: Tuple[str, ...] = ()
    unresolved_reference_ids: Tuple[str, ...] = ()

    def stored_reference_values(self) -> Tuple[str, ...]:
        return _unique(
            value
            for field in attr.fields(ReferenceSearchIdentities)
            for value in getattr(self, field.name)
        )

    def merge(self, other: "ReferenceSearchIdentities") -> "ReferenceSearchIdentities":
        return ReferenceSearchIdentities(
            **{
                field.name: _unique(
                    [*getattr(self, field.name), *getattr(other, field.name)]
                )
                for field in attr.fields(ReferenceSearchIdentities)
            }
        )

    def keep(self, predicate: Callable[[str], bool]) -> "ReferenceSearchIdentities":
        return ReferenceSearchIdentities(
            **{
                field.name: tuple(filter(predicate, getattr(self, field.name)))
                for field in attr.fields(ReferenceSearchIdentities)
            }
        )


def identities_of(entry: Mapping) -> ReferenceSearchIdentities:
    aliases = entry.get("aliases")
    alias_records = [
        alias
        for alias in (aliases if isinstance(aliases, (list, tuple)) else ())
        if isinstance(alias, Mapping)
    ]
    return ReferenceSearchIdentities(
        bibliography_ids=(entry["id"],),
        citation_keys=_strings([entry.get("citationKey")]),
        alias_values=_strings(alias.get("value") for alias in alias_records),
        normalized_alias_values=_strings(
            alias.get("normalizedValue") for alias in alias_records
        ),
    )


def requested_identities(id_: str, entry: Mapping) -> ReferenceSearchIdentities:
    entry_identities = identities_of(entry)
    if id_ in entry_identities.stored_reference_values():
        return ReferenceSearchIdentities()
    return ReferenceSearchIdentities(alias_values=(id_,))
