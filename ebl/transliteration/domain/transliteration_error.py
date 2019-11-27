class TransliterationError(Exception):
    def __init__(self, errors):
        super().__init__("Invalid transliteration")
        self.errors = errors
