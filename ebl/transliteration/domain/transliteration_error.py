class TransliterationError(Exception):
    def __init__(self, errors):
        super().__init__("Invalid transliteration")
        self.errors = errors

class DuplicateLabelError(Exception):
    def __init__(self, errors):
        super().__init__("Duplicate labels")
        self.errors = errors
