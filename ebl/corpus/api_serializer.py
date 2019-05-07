from parsy import ParseError

from ebl.corpus.text import Text, ManuscriptLine
from ebl.corpus.text_serializer import TextSerializer, TextDeserializer
from ebl.errors import DataError
from ebl.text.labels import LineNumberLabel, Label
from ebl.text.text_parser import TEXT_LINE


class ApiSerializer(TextSerializer):

    def __init__(self, include_documents=True):
        super().__init__(include_documents)

    def visit_manuscript_line(self, manuscript_line: ManuscriptLine) -> None:
        line = manuscript_line.line
        self.line['manuscripts'].append({
            'manuscriptId': manuscript_line.manuscript_id,
            'labels': [label.to_value() for label in manuscript_line.labels],
            'number': line.line_number.to_value(),
            'atf': line.atf[len(line.line_number.to_atf()) + 1:]
        })


class ApiDeserializer(TextDeserializer):

    def deserialize_manuscript_line(self,
                                    manuscript_line: dict) -> ManuscriptLine:
        line_number = LineNumberLabel(manuscript_line['number']).to_atf()
        atf = manuscript_line['atf']
        line = TEXT_LINE.parse(f'{line_number} {atf}')
        return ManuscriptLine(
            manuscript_line['manuscriptId'],
            tuple(Label.parse(label) for label in manuscript_line['labels']),
            line
        )


def serialize(text: Text) -> dict:
    return ApiSerializer.serialize(text, True)


def deserialize(dto: dict) -> Text:
    try:
        return ApiDeserializer.deserialize(dto)
    except (ValueError, ParseError) as error:
        raise DataError(error)
