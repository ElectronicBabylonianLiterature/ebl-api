from ebl.sign_list.value_mapper import ValueMapper


class SignList:

    def __init__(self, sign_repository):
        self._repository = sign_repository
        self._value_mapper = ValueMapper(sign_repository)

    def create(self, sign):
        return self._repository.create(sign)

    def find(self, sign_name):
        return self._repository.find(sign_name)

    def search(self, reading, sub_index):
        return self._repository.search(reading, sub_index)

    def map_transliteration(self, cleaned_transliteration):
        return [
            (
                [self._value_mapper.map(value) for value in row.split(' ')]
                if row
                else ['']
            )
            for row in cleaned_transliteration
        ]
