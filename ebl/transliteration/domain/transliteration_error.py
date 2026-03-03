from typing import Sequence, List


class ErrorAnnotation:
    def __init__(self, description: str, line_number: int):
        self.description = description
        self.line_number = line_number

    def to_dict(self) -> dict:
        return {
            "description": self.description,
            "lineNumber": self.line_number,
        }


class TransliterationError(Exception):
    label = "Invalid transliteration"

    def __init__(self, errors: Sequence[ErrorAnnotation]):
        super().__init__(self.label)
        self.errors: List[dict] = [error.to_dict() for error in errors]


class DuplicateLabelError(TransliterationError):
    label = "Duplicate labels"


class ExtentLabelError(TransliterationError):
    label = "Invalid extents"
