import json

import attr
from marshmallow import EXCLUDE

from ebl.ebl_ai_client import EblAiClient
from ebl.fragmentarium.application.annotations_schema import AnnotationsSchema
from ebl.fragmentarium.application.annotations_service import AnnotationsService
from ebl.fragmentarium.application.cropped_sign_image import Base64, CroppedSignImage
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.domain.annotation import Annotations
from ebl.tests.conftest import create_test_photo
from ebl.tests.factories.annotation import (
    AnnotationsFactory,
    AnnotationFactory,
    AnnotationDataFactory,
    CroppedSignFactory,
)
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber
from functools import singledispatchmethod
from itertools import combinations, groupby, zip_longest
from typing import Callable, Iterable, List, Mapping, Sequence, Tuple, Type

import attr

from ebl.lemmatization.domain.lemmatization import Lemmatization, LemmatizationError
from ebl.merger import Merger
from ebl.transliteration.domain.at_line import ColumnAtLine, ObjectAtLine, SurfaceAtLine
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION, Atf
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.line_label import LineLabel
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.translation_line import Extent, TranslationLine

SCHEMA = AnnotationsSchema()


def labels1(lines) -> Sequence[LineLabel]:
    current: LineLabel = LineLabel(None, None, None, None)
    labels: List[LineLabel] = []

    handlers: Mapping[
        Type[Line], Callable[[Line], Tuple[LineLabel, List[LineLabel]]]
    ] = {
        TextLine: lambda line: (
            current,
            [*labels, [current.set_line_number(line.line_number), str(type(line))]],
        ),
        ColumnAtLine: lambda line: (current.set_column(line.column_label), [*labels, [current, str(type(line))]]),
        SurfaceAtLine: lambda line: (
            current.set_surface(line.surface_label),
            [*labels, [current, str(type(line))]],
        ),
        ObjectAtLine: lambda line: (current.set_object(line.label), [*labels, [current, str(type(line))]]),
    }

    for line in lines:
        if type(line) in handlers:
            current, labels = handlers[type(line)](line)
        elif type(line) != NoteLine:
            current, labels = current, [*labels, [current, str(type(line))]]
    return labels

def test_123(fragment_repository):
    raw = json.load(open("./ex.json"))
    fragment = FragmentSchema(unknown=EXCLUDE).load(raw)
    fragment_repository.create(fragment)
    assert fragment == fragment_repository.query_by_museum_number(fragment.number)
    labels = labels1(fragment.text.lines)
    asd = [label[1] for label in labels]
    print(asd)
    assert False

def test_1234(fragment_repository):
    raw = json.load(open("./ex.json"))
    fragment = FragmentSchema(unknown=EXCLUDE).load(raw)
    fragment_repository.create(fragment)
    exp_frag = fragment_repository.query_by_museum_number(fragment.number)
    assert fragment == fragment_repository.query_by_museum_number(fragment.number)


def test_cropped_images_from_sign(
    annotations_repository,
    fragment_repository,
    photo_repository,
    when,
    text_with_labels,
    annotations_service,
):
    single_annotation = AnnotationFactory.build(
        data=AnnotationDataFactory.build(path=[2, 0, 0])
    )
    annotation = AnnotationsFactory.build(annotations=[single_annotation])

    fragment = TransliteratedFragmentFactory.build(text=text_with_labels)
    (
        when(fragment_repository)
        .query_by_museum_number(annotation.fragment_number)
        .thenReturn(fragment)
    )
    (
        when(photo_repository)
        .query_by_file_name(f"{annotation.fragment_number}.jpg")
        .thenReturn(create_test_photo("K.2"))
    )

    annotations, cropped_images = annotations_service._cropped_image_from_annotations(
        annotation
    )
    for annotation, cropped_image in zip(annotations.annotations, cropped_images):
        assert annotation.cropped_sign.image_id == cropped_image.image_id
        assert annotation.cropped_sign.label == "i Stone wig Stone wig 2"


def test_generate_annotations(
    annotations_repository,
    photo_repository,
    changelog,
    when,
    fragment_repository,
    cropped_sign_images_repository,
):
    fragment_number = MuseumNumber.of("X.0")

    image_file = create_test_photo("K.2")

    when(photo_repository).query_by_file_name(f"{fragment_number}.jpg").thenReturn(
        image_file
    )
    ebl_ai_client = EblAiClient("mock-localhost:8001")
    service = AnnotationsService(
        ebl_ai_client,
        annotations_repository,
        photo_repository,
        changelog,
        fragment_repository,
        photo_repository,
        cropped_sign_images_repository,
    )
    expected = Annotations(fragment_number, tuple())
    when(ebl_ai_client).generate_annotations(fragment_number, image_file, 0).thenReturn(
        expected
    )

    annotations = service.generate_annotations(fragment_number, 0)
    assert isinstance(annotations, Annotations)
    assert annotations == expected


def test_find(annotations_repository, annotations_service, when):
    annotations = AnnotationsFactory.build()
    when(annotations_repository).query_by_museum_number(
        annotations.fragment_number
    ).thenReturn(annotations)

    assert annotations_service.find(annotations.fragment_number) == annotations


def test_update(
    annotations_service,
    annotations_repository,
    photo_repository,
    fragment_repository,
    cropped_sign_images_repository,
    when,
    user,
    changelog,
    text_with_labels,
):
    fragment_number = MuseumNumber("K", "1")
    fragment = TransliteratedFragmentFactory(
        number=fragment_number, text=text_with_labels
    )

    old_annotations = AnnotationsFactory.build(fragment_number=fragment_number)

    data = AnnotationDataFactory.build(path=[2, 0, 0])
    annotation = AnnotationFactory.build(cropped_sign=None, data=data)
    annotations = AnnotationsFactory.build(
        fragment_number=fragment_number, annotations=[annotation]
    )

    when(annotations_repository).query_by_museum_number(fragment_number).thenReturn(
        old_annotations
    )
    image = create_test_photo("K.2")
    when(fragment_repository).query_by_museum_number(fragment_number).thenReturn(
        fragment
    )
    (
        when(photo_repository)
        .query_by_file_name(f"{annotations.fragment_number}.jpg")
        .thenReturn(image)
    )

    expected_cropped_sign_image = CroppedSignImage("test-id", Base64("test-image"))
    annotation_cropped_sign = attr.evolve(
        annotation,
        cropped_sign=CroppedSignFactory.build(
            image_id="test-id",
            label="i Stone wig Stone wig 2",
        ),
    )
    expected_annotations = attr.evolve(
        annotations, annotations=[annotation_cropped_sign]
    )
    when(CroppedSignImage).create(...).thenReturn(expected_cropped_sign_image)

    when(annotations_repository).create_or_update(expected_annotations).thenReturn()
    when(cropped_sign_images_repository).create_many(
        [expected_cropped_sign_image]
    ).thenReturn()
    schema = AnnotationsSchema()
    when(changelog).create(
        "annotations",
        user.profile,
        {"_id": str(fragment_number), **schema.dump(old_annotations)},
        {"_id": str(fragment_number), **schema.dump(expected_annotations)},
    ).thenReturn()

    result = annotations_service.update(annotations, user)
    assert result == expected_annotations
