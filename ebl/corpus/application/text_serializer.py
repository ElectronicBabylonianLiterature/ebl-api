from ebl.corpus.application.schemas import TextSchema
from ebl.corpus.domain.text import Text


def serialize(text: Text) -> dict:
    return TextSchema().dump(text)  # pyre-ignore[16]


def deserialize(data: dict) -> Text:
    return TextSchema().load(data)  # pyre-ignore[16]
