import time
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


def preview_wire_line() -> dict:
    fragment = TransliteratedFragmentFactory.build()
    return matching_line_preview_of_data(dumped_text(fragment.text), (0,))["lines"][0]


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


@pytest.mark.parametrize(
    "missing_field", ["lineNumber", "prefix", "content", "index", "type"]
)
def test_preview_line_schema_rejects_missing_required_fields(missing_field):
    wire_line = preview_wire_line()

    with pytest.raises(ValidationError):
        FragmentQueryPreviewLineSchema().load(
            {key: value for key, value in wire_line.items() if key != missing_field}
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("type", "EmptyLine"),
        ("index", "first"),
        ("lineNumber", "1."),
        ("prefix", 1),
        ("content", {"type": "Word"}),
        ("content", ["Word"]),
    ],
)
def test_preview_line_schema_rejects_invalid_line_shape(field, value):
    with pytest.raises(ValidationError):
        FragmentQueryPreviewLineSchema().load({**preview_wire_line(), field: value})


def test_preview_line_schema_dumps_stored_content_unchanged():
    wire_line = preview_wire_line()
    schema = FragmentQueryPreviewLineSchema()

    dumped_line = cast(dict, schema.dump(schema.load(wire_line)))

    assert dumped_line["content"] == wire_line["content"]
    assert dumped_line["lineNumber"] == wire_line["lineNumber"]


def test_preview_line_schema_page_cost_stays_line_level():
    wire_lines = [preview_wire_line() for _ in range(40)] * 25
    schema = FragmentQueryPreviewLineSchema(many=True)

    started = time.perf_counter()
    schema.dump(schema.load(wire_lines))
    elapsed = time.perf_counter() - started

    assert len(wire_lines) == 1000
    assert elapsed < 0.5
