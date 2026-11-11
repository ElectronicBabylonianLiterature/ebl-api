from dataclasses import dataclass
from typing import Any, Callable, Dict, FrozenSet, Mapping, Optional, Sequence, cast

from ebl.corpus.application.schemas import ChapterSchema
from ebl.io.sparse_tokens.token_keys import dropped_token_keys, needs_sparse_rewrite
from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.transliteration.application.storage_serialization import (
    storage_serialization,
)
from ebl.transliteration.application.text_schema import TextSchema

STORED_SIZE = "__storedSize"


@dataclass(frozen=True)
class TokenFields:
    collection: str
    fields: Sequence[str]
    load: Callable[[Mapping[str, Any]], object]
    dump: Callable[[object], Dict[str, Any]]
    whole_document: bool


@dataclass(frozen=True)
class Rewrite:
    fields: Dict[str, Any]
    lossless: bool
    dropped_keys: FrozenSet[str]


def load_fragment_text(document: Mapping[str, Any]) -> object:
    return TextSchema().load(document["text"])


def dump_fragment_text(text: object) -> Dict[str, Any]:
    return {"text": TextSchema().dump(text)}


def dump_chapter_lines(chapter: object) -> Dict[str, Any]:
    return cast(
        Dict[str, Any], ChapterSchema(only=["lines", "manuscripts"]).dump(chapter)
    )


def fragment_token_fields() -> TokenFields:
    return TokenFields(
        collection="fragments",
        fields=("text",),
        load=load_fragment_text,
        dump=dump_fragment_text,
        whole_document=False,
    )


def chapter_token_fields(provenance_service: ProvenanceService) -> TokenFields:
    def load(document: Mapping[str, Any]) -> object:
        return ChapterSchema(context={"provenance_service": provenance_service}).load(
            document
        )

    return TokenFields(
        collection="chapters",
        fields=("lines", "manuscripts"),
        load=load,
        dump=dump_chapter_lines,
        whole_document=True,
    )


def canonical(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: sorted(item)
            if key == "enclosureType" and isinstance(item, list)
            else canonical(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [canonical(item) for item in value]
    return value


def stored_fields(spec: TokenFields, document: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: document[key] for key in spec.fields if key in document}


def loadable(document: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        key: value for key, value in document.items() if key not in ("_id", STORED_SIZE)
    }


def rewrite_document(
    spec: TokenFields, document: Mapping[str, Any], full_check: bool = False
) -> Optional[Rewrite]:
    original = stored_fields(spec, document)
    if len(original) < len(spec.fields):
        return None
    if not (full_check or needs_sparse_rewrite(original)):
        return None
    source = loadable(document)
    loaded = spec.load(source)
    with storage_serialization():
        rewritten = spec.dump(loaded)
    if canonical(rewritten) == canonical(original):
        return None
    return Rewrite(
        fields=rewritten,
        lossless=spec.load({**source, **rewritten}) == loaded,
        dropped_keys=dropped_token_keys(original, rewritten),
    )
