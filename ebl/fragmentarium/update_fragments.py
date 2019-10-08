import attr
from progress.bar import Bar

from ebl.app import create_context
from ebl.signs.infrastructure.menoizing_sign_repository \
    import MemoizingSignRepository
from ebl.transliteration.domain.lemmatization import LemmatizationError
from ebl.transliteration.domain.transliteration_error import \
    TransliterationError
from ebl.users.domain.user import ApiUser


def update_fragment(transliteration_factory, updater, fragment):
    transliteration = transliteration_factory.create(
        fragment.text.atf,
        fragment.notes
    )
    user = ApiUser('update_fragments.py')
    updater.update_transliteration(fragment.number,
                                   transliteration,
                                   user)


def find_transliterated(fragment_repository):
    return [
        fragment.number for fragment
        in fragment_repository.find_transliterated()
    ]


class State:
    def __init__(self):
        self.invalid_atf = 0
        self.invalid_lemmas = 0
        self.updated = 0
        self.errors = []

    def add_updated(self):
        self.updated += 1

    def add_lemmatization_error(self, error, fragment):
        self.invalid_lemmas += 1
        self.errors.append(f'{fragment.number}\t{error}')

    def add_transliteration_error(self, transliteration_error, fragment):
        self.invalid_atf += 1
        for index, error in enumerate(transliteration_error.errors):
            atf = fragment.text.lines[error['lineNumber'] - 1].atf
            number = (fragment.number
                      if index == 0 else
                      len(fragment.number) * ' ')
            self.errors.append(f'{number}\t{atf}')

    def to_tsv(self):
        return '\n'.join([
            *self.errors,
            f'# Updated fragments: {self.updated}',
            f'# Invalid ATF: {self.invalid_atf}',
            f'# Invalid lemmas: {self.invalid_lemmas}',
        ])


def update_fragments(fragment_repository,
                     transliteration_factory,
                     updater):
    state = State()
    numbers = find_transliterated(fragment_repository)

    with Bar('Updating', max=len(numbers)) as bar:
        for number in numbers:
            try:
                fragment = fragment_repository.query_by_fragment_number(number)
                update_fragment(transliteration_factory,
                                updater,
                                fragment)
                state.add_updated()
            except TransliterationError as error:
                state.add_transliteration_error(error, fragment)
            except LemmatizationError as error:
                state.add_lemmatization_error(error, fragment)

            bar.next()

    with open('invalid_fragments.tsv', 'w', encoding='utf-8') as file:
        file.write(state.to_tsv())


if __name__ == '__main__':
    context = create_context()
    context = attr.evolve(context, sign_repository=MemoizingSignRepository(
        context.sign_repository
    ))
    update_fragments(context.fragment_repository,
                     context.get_transliteration_update_factory(),
                     context.get_fragment_updater())
