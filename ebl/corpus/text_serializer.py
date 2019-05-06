from ebl.corpus.text import TextVisitor, Text, Chapter, Manuscript, \
    ManuscriptLine, Line


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
            'reconstruction': line.reconstruction,
            'manuscripts': []
        }
        self.chapter['lines'].append(self.line)

    def visit_manuscript_line(self, manuscript_line: ManuscriptLine) -> None:
        self.line['manuscripts'].append({
            'manuscriptId': manuscript_line.manuscript_id,
            'labels': [label.to_value() for label in manuscript_line.labels],
            'line': manuscript_line.line.to_dict()
        })
