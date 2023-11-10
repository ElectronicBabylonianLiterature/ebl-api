class ErrorAnnotation:
    def __init__(self, description: str, line_number: int):
        self.description = description
        self.line_number = line_number

    def to_dict(self):
        return {
            "description": self.description,
            "lineNumber": self.line_number,
        }


class TransliterationError(Exception):
    label = "Invalid transliteration"

    def __init__(self, errors):
        super().__init__(self.label)
        self.errors = errors


class DuplicateLabelError(TransliterationError):
    label = "Duplicate labels"


class ExtentLabelError(TransliterationError):
    label = "Invalid extents"
