from ebl.corpus.web.display_schemas import ManuscriptLineDisplaySchema
from ebl.tests.factories.corpus import ChapterFactory
from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema


def test_serialize():
    chapter = ChapterFactory.build()
    line = chapter.lines[0].variants[0].manuscripts[0]
    manuscript = chapter.get_manuscript(line.manuscript_id)
    schema = ManuscriptLineDisplaySchema(context={"manuscripts": chapter.manuscripts})

    assert schema.dump(line) == {
        "siglumDisambiguator": manuscript.siglum_disambiguator,
        "periodModifier": manuscript.period_modifier.value,
        "period": manuscript.period.long_name,
        "provenance": manuscript.provenance.long_name,
        "type": manuscript.type.long_name,
        "labels": [label.to_value() for label in line.labels],
        "line": OneOfLineSchema().dump(line.line),
        "paratext": OneOfLineSchema().dump(line.paratext, many=True),
    }
