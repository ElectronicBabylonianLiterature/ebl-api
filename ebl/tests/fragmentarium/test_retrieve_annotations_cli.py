import argparse
import json
import runpy
import sys
from pathlib import Path
from typing import List

import pytest

from ebl import app
from ebl.fragmentarium import retrieve_annotations, retrieve_annotations_helpers
from ebl.fragmentarium.domain.annotation import AnnotationValueType
from ebl.tests.factories.annotation import AnnotationsFactory

ANNOTATIONS_JSON = Path("ebl/fragmentarium/annotations.json")
MODULE = "ebl.fragmentarium.retrieve_annotations"


class _Recorder:
    def __init__(self) -> None:
        self.collections: List[list] = []
        self.filters: List[list] = []

    def create_annotations(self, collection, _oa, _oi, _photos, to_filter=()) -> None:
        self.collections.append(list(collection))
        self.filters.append(list(to_filter))


@pytest.fixture
def cli(monkeypatch, tmp_path):
    recorder = _Recorder()
    annotations = [
        AnnotationsFactory.build(
            fragment_number=json.loads(ANNOTATIONS_JSON.read_text(encoding="utf-8"))[
                "finished"
            ][0]
        ),
        AnnotationsFactory.build(fragment_number="NOT.IN.THE.LIST"),
    ]

    class _Context:
        annotations_repository = type(
            "Repo", (), {"retrieve_all_non_empty": staticmethod(lambda: annotations)}
        )()
        photo_repository = object()

    monkeypatch.setattr(app, "create_context", lambda: _Context())
    monkeypatch.setattr(retrieve_annotations, "create_context", lambda: _Context())
    for module in (retrieve_annotations, retrieve_annotations_helpers):
        monkeypatch.setattr(
            module, "create_annotations", recorder.create_annotations, raising=False
        )
        monkeypatch.setattr(
            module, "write_fragment_numbers", lambda *a, **k: None, raising=False
        )
        monkeypatch.setattr(
            module, "create_directory", lambda *a, **k: None, raising=False
        )
    return recorder, annotations


def test_the_finished_filter_keeps_only_listed_fragments(cli) -> None:
    recorder, annotations = cli

    retrieve_annotations.main(["-oa", "/out/a", "-oi", "/out/i", "-f", "finished"])

    assert recorder.collections == [[annotations[0]]]


def test_the_unfinished_filter_keeps_only_unlisted_fragments(cli) -> None:
    recorder, annotations = cli

    retrieve_annotations.main(["-oa", "/out/a", "-oi", "/out/i", "-f", "unfinished"])

    assert recorder.collections == [[annotations[1]]]


def test_an_unknown_filter_is_rejected(cli) -> None:
    with pytest.raises(argparse.ArgumentError, match="Filter has to be either"):
        retrieve_annotations.main(["-oa", "/out/a", "-oi", "/out/i", "-f", "bogus"])


def test_classification_filters_more_annotation_types(cli) -> None:
    recorder, _ = cli

    retrieve_annotations.main(["-oa", "/out/a", "-oi", "/out/i", "-c"])
    classification = recorder.filters[-1]

    retrieve_annotations.main(["-oa", "/out/a", "-oi", "/out/i"])
    detection = recorder.filters[-1]

    assert AnnotationValueType.SURFACE_AT_LINE in classification
    assert AnnotationValueType.SURFACE_AT_LINE not in detection
    assert set(detection) < set(classification)


def test_the_mongo_fallback_needs_a_connection_string(monkeypatch, cli) -> None:
    monkeypatch.delenv("MONGODB_URI", raising=False)
    monkeypatch.setattr(
        retrieve_annotations,
        "create_context",
        lambda: (_ for _ in ()).throw(KeyError("EBL_AI_API")),
    )

    with pytest.raises(RuntimeError, match="Missing required environment variable"):
        retrieve_annotations.main(["-oa", "/out/a", "-oi", "/out/i"])


def test_running_the_module_as_a_script_invokes_main(monkeypatch, cli) -> None:
    recorder, annotations = cli
    monkeypatch.setattr(sys, "argv", [MODULE, "-oa", "/out/a", "-oi", "/out/i"])

    runpy.run_module(MODULE, run_name="__main__")

    assert recorder.collections[-1] == annotations
