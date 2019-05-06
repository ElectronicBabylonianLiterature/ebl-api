from ebl.corpus.text import Text
from ebl.corpus.text_serializer import TextSerializer


def serialize(text: Text) -> dict:
    return TextSerializer.serialize(text, False)


def deserialize(dictionary: dict) -> Text:
    return Text.from_dict(dictionary)
