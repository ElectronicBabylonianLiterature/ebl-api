import itertools
from typing import Mapping, Sequence

import pydash

import ebl.corpus.domain.chapter
from ebl.corpus.domain.line import Line, ManuscriptLineLabel
from ebl.corpus.domain.manuscript import Manuscript
from ebl.transliteration.domain.line_number import AbstractLineNumber


def validate_manuscript_ids(_instance, _attribute, value: Sequence[Manuscript]) -> None:
    duplicate_ids = pydash.duplicates([manuscript.id for manuscript in value])
    if duplicate_ids:
        raise ValueError(f"Duplicate manuscript IDs: {duplicate_ids}.")


def validate_manuscript_sigla(
    _instance, _attribute, value: Sequence[Manuscript]
) -> None:
    duplicate_sigla = pydash.duplicates([manuscript.siglum for manuscript in value])
    if duplicate_sigla:
        raise ValueError(f"Duplicate sigla: {duplicate_sigla}.")


def validate_line_numbers(_instance, _attribute, value: Sequence[Line]) -> None:
    duplicates = pydash.duplicates([line.number for line in value])
    if any(duplicates):
        raise ValueError(f"Duplicate line numbers: {duplicates}.")


def validate_translations(_instance, _attribute, value: Sequence[Line]) -> None:
    line_numbers = {line.number: index for index, line in enumerate(value)}
    _validate_extents(line_numbers, value)
    _validate_extent_ranges(line_numbers, value)


def _validate_extents(
    line_numbers: Mapping[AbstractLineNumber, int], value: Sequence[Line]
) -> None:
    errors = [
        f"Invalid extent {translation.extent} in line {line.number.label}."
        for index, line in enumerate(value)
        for translation in line.translation
        if translation.extent
        and line_numbers.get(translation.extent.number, -1) <= index
    ]

    if errors:
        raise ValueError(" ".join(errors))


def _validate_extent_ranges(
    line_numbers: Mapping[AbstractLineNumber, int], value: Sequence[Line]
) -> None:
    ranges = itertools.groupby(
        sorted(
            (
                (
                    translation.language,
                    set(
                        range(
                            index,
                            (
                                line_numbers[translation.extent.number]
                                if translation.extent
                                else index
                            )
                            + 1,
                        )
                    ),
                )
                for index, line in enumerate(value)
                for translation in line.translation
            ),
            key=lambda pair: pair[0],
        ),
        lambda pair: pair[0],
    )

    range_errors = [
        f"Overlapping extents for language {key}."
        for key, group in ranges
        if any(
            pair[0][1] & pair[1][1] for pair in itertools.combinations(list(group), 2)
        )
    ]

    if range_errors:
        raise ValueError(" ".join(range_errors))


def validate_orphan_manuscript_ids(
    instance: "ebl.corpus.domain.chapter.Chapter", _, value: Sequence[Line]
) -> None:
    manuscript_ids = {manuscript.id for manuscript in instance.manuscripts}
    used_manuscripts_ids = {
        manuscript_id
        for line in instance.lines
        for manuscript_id in line.manuscript_ids
    }
    orphans = used_manuscripts_ids - manuscript_ids
    if orphans:
        raise ValueError(f"Missing manuscripts: {orphans}.")


def validate_manuscript_line_labels(
    instance: "ebl.corpus.domain.chapter.Chapter", _, value: Sequence[Line]
) -> None:
    duplicates = pydash.duplicates(instance.manuscript_line_labels)
    if duplicates:
        readable_labels = _make_labels_readable(instance, duplicates)
        raise ValueError(f"Duplicate manuscript line labels: {readable_labels}.")


def _make_labels_readable(
    instance: "ebl.corpus.domain.chapter.Chapter", labels: Sequence[ManuscriptLineLabel]
) -> str:
    return ", ".join(
        " ".join(
            [
                str(instance.get_manuscript(label[0]).siglum),
                *[side.to_value() for side in label[1]],
                label[2].label,
            ]
        )
        for label in labels
    )
