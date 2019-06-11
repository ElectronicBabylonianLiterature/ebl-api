from parsy import ParseError

from ebl.corpus.text import Text, ManuscriptLine, Line
from ebl.corpus.text_serializer import TextSerializer, TextDeserializer
from ebl.errors import DataError
from ebl.text.labels import LineNumberLabel, Label
from ebl.text.reconstructed_text import AkkadianWord, Lacuna, \
    MetricalFootSeparator, Caesura, ReconstructionToken
from ebl.text.text_parser import TEXT_LINE


class ApiSerializer(TextSerializer):

    def __init__(self, include_documents=True):
        super().__init__(include_documents)

    @staticmethod
    def serialize_public(text: Text):
        serializer = ApiSerializer(False)
        serializer.visit_text(text)
        return serializer.text

    def visit_manuscript_line(self, manuscript_line: ManuscriptLine) -> None:
        line = manuscript_line.line
        self.line['manuscripts'].append({
            'manuscriptId': manuscript_line.manuscript_id,
            'labels': [label.to_value() for label in manuscript_line.labels],
            'number': line.line_number.to_value(),
            'atf': line.atf[len(line.line_number.to_atf()) + 1:],
            'atfTokens': manuscript_line.line.to_dict()['content']
        })

    def visit_line(self, line: Line) -> None:
        super().visit_line(line)
        self.line['reconstructionTokens'] = []

    def visit_akkadian_word(self, word: AkkadianWord):
        self._visit_reconstruction_token('AkkadianWord', word)

    def visit_lacuna(self, lacuna: Lacuna) -> None:
        self._visit_reconstruction_token('Lacuna', lacuna)

    def visit_metrical_foot_separator(
            self,
            separator: MetricalFootSeparator
    ) -> None:
        self._visit_reconstruction_token('MetricalFootSeparator', separator)

    def visit_caesura(self, caesura: Caesura) -> None:
        self._visit_reconstruction_token('Caesura', caesura)

    def _visit_reconstruction_token(self,
                                    type: str,
                                    token: ReconstructionToken) -> None:
        self.line['reconstructionTokens'].append({
            'type': type,
            'value': str(token)
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


def serialize(text: Text, include_documents=True) -> dict:
    return ApiSerializer.serialize(text, include_documents)


def deserialize(dto: dict) -> Text:
    try:
        return ApiDeserializer.deserialize(dto)
    except (ValueError, ParseError) as error:
        raise DataError(error)
