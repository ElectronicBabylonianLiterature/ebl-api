from ebl.corpus.application.text_serializer import TextDeserializer, \
    TextSerializer
from ebl.corpus.domain.text import Text


def serialize(text: Text) -> dict:
    return TextSerializer.serialize(text, False)


def deserialize(dictionary: dict) -> Text:
    return TextDeserializer.deserialize(dictionary)
