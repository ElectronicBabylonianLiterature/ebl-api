from typing import cast

import pytest
from marshmallow import ValidationError

from ebl.fragmentarium.application.fragment_query_preview import (
    matching_line_preview_of_data,
)
from ebl.fragmentarium.application.fragment_query_summary_schema import (
    FragmentQueryPreviewLineSchema,
)
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.tests.fragmentarium.fragment_query_preview_test_helpers import dumped_text


def test_preview_line_schema_roundtrip_preserves_rich_line_shape():
    fragment = TransliteratedFragmentFactory.build()
    stored_text = dumped_text(fragment.text)
    stored_text["lines"][0]["storedOnly"] = True
    wire_line = matching_line_preview_of_data(stored_text, (0,))["lines"][0]
    schema = FragmentQueryPreviewLineSchema()

    loaded = cast(dict, schema.load(wire_line))

    assert schema.dump(loaded) == {
        key: value for key, value in wire_line.items() if key != "storedOnly"
    }
    assert "line_number" in loaded
    assert "lineNumber" not in loaded
    assert "storedOnly" not in schema.dump(loaded)


def test_preview_line_schema_derives_missing_prefix_from_line_number():
    fragment = TransliteratedFragmentFactory.build()
    wire_line = matching_line_preview_of_data(dumped_text(fragment.text), (0,))[
        "lines"
    ][0]
    wire_line.pop("prefix")
    schema = FragmentQueryPreviewLineSchema()

    loaded = cast(dict, schema.load(wire_line))

    assert "prefix" not in loaded
    assert cast(dict, schema.dump(loaded))["prefix"] == (
        fragment.text.lines[0].line_number.atf
    )


@pytest.mark.parametrize("missing_field", ["lineNumber", "content", "index", "type"])
def test_preview_line_schema_rejects_missing_required_fields(missing_field):
    fragment = TransliteratedFragmentFactory.build()
    wire_line = matching_line_preview_of_data(dumped_text(fragment.text), (0,))[
        "lines"
    ][0]

    with pytest.raises(ValidationError):
        FragmentQueryPreviewLineSchema().load(
            {key: value for key, value in wire_line.items() if key != missing_field}
        )
