from ebl.sign_list.value_mapper import create_value_mapper


class SignList:

    def __init__(self, sign_repository):
        self._repository = sign_repository
        self._map_value = create_value_mapper(sign_repository)

    def create(self, sign):
        return self._repository.create(sign)

    def find(self, sign_name):
        return self._repository.find(sign_name)

    def search(self, reading, sub_index):
        return self._repository.search(reading, sub_index)

    def map_transliteration(self, cleaned_transliteration):
        return [
            (
                [self._map_value(value) for value in row.split(' ')]
                if row
                else ['']
            )
            for row in cleaned_transliteration
        ]
