from typing import Tuple, Optional

import attr

from ebl.app import create_context
from ebl.fragmentarium.application.annotations_repository import AnnotationsRepository
from ebl.fragmentarium.domain.annotation import Annotation, AnnotationValueType
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.lark_parser import parse_word
from ebl.transliteration.domain.sign_tokens import NamedSign


def parse_value(value) -> Tuple[str, Optional[int]]:
    word = parse_word(value)
    assert len(word.parts) == 1
    token = word.parts[0]
    if isinstance(token, NamedSign):
        return token.name.lower(), token.sub_index
    else:
        raise Exception(f"'{token}' object is not an instance of 'NamedSign'")


def update_annotation_annotation(
    sign_repository: SignRepository, annotation_annotation: Annotation
) -> Annotation:
    sign = sign_repository.search(*parse_value(annotation_annotation.data.value))
    if not sign:
        print(
            f"No sign corresponding to reading: '{annotation_annotation.data.value}' "
            f"with id: '{annotation_annotation.data.id}'"
            f"with fragmentNumber: '{fragment_number}'"
        )
        return annotation_annotation
    return attr.evolve(
        annotation_annotation,
        data=attr.evolve(
            annotation_annotation.data,
            sign_name=sign.name,
            type=AnnotationValueType.HAS_SIGN,
        ),
    )


def update_annotations(
    annotations_repository: AnnotationsRepository, sign_repository: SignRepository
) -> None:
    annotation_collection = annotations_repository.retrieve_all()
    for counter, annotation in enumerate(annotation_collection):
        new_annotation_annotations = []
        for annotation_annotation in annotation.annotations:
            if annotation_annotation.data.value == "blank":
                new_annotation_annotations.append(
                    attr.evolve(
                        annotation_annotation,
                        data=attr.evolve(
                            annotation_annotation.data,
                            sign_name="",
                            type=AnnotationValueType.BLANK,
                        ),
                    )
                )
            elif (
                annotation_annotation.data.sign_name
                or annotation_annotation.data.type != AnnotationValueType.HAS_SIGN
            ):
                new_annotation_annotations.append(annotation_annotation)
            else:
                new_annotation_annotations.append(
                    update_annotation_annotation(sign_repository, annotation_annotation)
                )
        new_annotation = attr.evolve(annotation, annotations=new_annotation_annotations)
        annotations_repository.create_or_update(new_annotation)
        print("{:5}".format(counter + 1), f" of {len(annotation_collection)}")


if __name__ == "__main__":
    context = create_context()
    update_annotations(context.annotations_repository, context.sign_repository)
    print("Done")
