import pydash
from parsy import ParseError

from ebl.corpus.text import Text, ManuscriptLine
from ebl.corpus.text_serializer import TextSerializer
from ebl.errors import DataError
from ebl.text.labels import LineNumberLabel
from ebl.text.text_parser import TEXT_LINE


class ApiSerializer(TextSerializer):
    # pylint: disable=R0903

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


def serialize(text: Text) -> dict:
    return ApiSerializer.serialize(text, True)


def deserialize(dto: dict) -> Text:
    def parse_manuscript(manuscript_dto: dict):
        try:
            atf_line_number =\
                LineNumberLabel(manuscript_dto['number']).to_atf()
            line = \
                TEXT_LINE.parse(f'{atf_line_number} {manuscript_dto["atf"]}')
        except (ParseError, ValueError) as error:
            raise DataError(error)

        return pydash.omit({
            **manuscript_dto,
            'line': line.to_dict()
        }, 'atf')

    parsed_media = {
        **dto,
        'chapters': [
            {
                **chapter,
                'lines': [
                    {
                        **line,
                        'manuscripts': [
                            parse_manuscript(manuscript)
                            for manuscript in line['manuscripts']
                        ]
                    } for line in chapter['lines']
                ]
            } for chapter in dto['chapters']
        ]
    }
    try:
        return Text.from_dict(parsed_media)
    except ValueError as error:
        raise DataError(error)
