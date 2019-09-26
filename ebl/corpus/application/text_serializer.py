from ebl.bibliography.domain.reference import Reference
from ebl.corpus.application.reconstructed_text_parser import \
    parse_reconstructed_line
from ebl.corpus.domain.enums import Classification, ManuscriptType, Period, \
    PeriodModifier, Provenance, Stage
from ebl.corpus.domain.text import Chapter, Line, Manuscript, ManuscriptLine, \
    Text, \
    TextVisitor
from ebl.transliteration.domain.labels import Label, LineNumberLabel
from ebl.transliteration.domain.line import TextLine
from ebl.transliteration.domain.text import create_tokens


class TextSerializer(TextVisitor):
    @classmethod
    def serialize(cls, text: Text, include_documents):
        serializer = cls(include_documents)
        text.accept(serializer)
        return serializer.text

    def __init__(self, include_documents):
        super().__init__(TextVisitor.Order.PRE)
        self._include_documents = include_documents
        self.text = None
        self.chapter = None
        self.manuscript = None
        self.line = None
        self.manuscript_line = None

    def visit_text(self, text: Text) -> None:
        self.text = {
            'category': text.category,
            'index': text.index,
            'name': text.name,
            'numberOfVerses': text.number_of_verses,
            'approximateVerses': text.approximate_verses,
            'chapters': []
        }

    def visit_chapter(self, chapter: Chapter) -> None:
        self.chapter = {
            'classification': chapter.classification.value,
            'stage': chapter.stage.value,
            'version': chapter.version,
            'name': chapter.name,
            'order': chapter.order,
            'manuscripts': [],
            'lines': []
        }
        self.text['chapters'].append(self.chapter)

    def visit_manuscript(self, manuscript: Manuscript) -> None:
        self.manuscript = {
            'id': manuscript.id,
            'siglumDisambiguator': manuscript.siglum_disambiguator,
            'museumNumber': manuscript.museum_number,
            'accession': manuscript.accession,
            'periodModifier': manuscript.period_modifier.value,
            'period': manuscript.period.long_name,
            'provenance': manuscript.provenance.long_name,
            'type': manuscript.type.long_name,
            'notes': manuscript.notes,
            'references': [
                reference.to_dict(self._include_documents)
                for reference in manuscript.references
            ]
        }
        self.chapter['manuscripts'].append(self.manuscript)

    def visit_line(self, line: Line) -> None:
        self.line = {
            'number': line.number.to_value(),
            'reconstruction': ' '.join(str(token)
                                       for token
                                       in line.reconstruction),
            'manuscripts': []
        }
        self.chapter['lines'].append(self.line)

    def visit_manuscript_line(self, manuscript_line: ManuscriptLine) -> None:
        self.line['manuscripts'].append({
            'manuscriptId': manuscript_line.manuscript_id,
            'labels': [label.to_value() for label in manuscript_line.labels],
            'line': manuscript_line.line.to_dict()
        })


class TextDeserializer:

    @classmethod
    def deserialize(cls, text: dict):
        return cls().deserialize_text(text)

    def deserialize_text(self, text: dict) -> Text:
        return Text(
            text['category'],
            text['index'],
            text['name'],
            text['numberOfVerses'],
            text['approximateVerses'],
            tuple(
                self.deserialize_chapter(chapter)
                for chapter in text['chapters']
            )
        )

    def deserialize_chapter(self, chapter: dict) -> Chapter:
        return Chapter(
            Classification(chapter['classification']),
            Stage(chapter['stage']),
            chapter['version'],
            chapter['name'],
            chapter['order'],
            tuple(
                self.deserialize_manuscript(manuscript)
                for manuscript in chapter['manuscripts']
            ),
            tuple(
                self.deserialize_line(line)
                for line in chapter.get('lines', [])
            )
        )

    def deserialize_manuscript(self, manuscript: dict) -> Manuscript:
        return Manuscript(
            manuscript['id'],
            manuscript['siglumDisambiguator'],
            manuscript['museumNumber'],
            manuscript['accession'],
            PeriodModifier(manuscript['periodModifier']),
            Period.from_name(manuscript['period']),
            Provenance.from_name(manuscript['provenance']),
            ManuscriptType.from_name(manuscript['type']),
            manuscript['notes'],
            tuple(
                Reference.from_dict(reference)
                for reference in manuscript['references']
            )
        )

    def deserialize_line(self, line: dict) -> Line:
        return Line(LineNumberLabel(line['number']),
                    parse_reconstructed_line(line['reconstruction']),
                    tuple(self.deserialize_manuscript_line(line)
                          for line in line['manuscripts']))

    def deserialize_manuscript_line(self,
                                    manuscript_line: dict) -> ManuscriptLine:
        return ManuscriptLine(
            manuscript_line['manuscriptId'],
            tuple(Label.parse(label) for label in manuscript_line['labels']),
            TextLine.of_iterable(
                LineNumberLabel.from_atf(manuscript_line['line']['prefix']),
                create_tokens(manuscript_line['line']['content'])
            )
        )


def serialize(text: Text) -> dict:
    return TextSerializer.serialize(text, False)


def deserialize(dictionary: dict) -> Text:
    return TextDeserializer.deserialize(dictionary)
