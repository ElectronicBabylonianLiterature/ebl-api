from dataclasses import dataclass

import pytest

from ebl.bibliography.application.bibliography import Bibliography
from ebl.errors import DataError
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.fragment import FragmentFactory
from ebl.users.domain.user import User

SCHEMA = FragmentSchema()


@dataclass(frozen=True)
class FragmentReferencesContext:
    fragment_updater: FragmentUpdater
    bibliography: Bibliography
    user: User
    fragment_repository: object
    parallel_line_injector: object
    changelog: object
    when: object


@pytest.fixture
def fragment_references_context(request: pytest.FixtureRequest):
    return FragmentReferencesContext(
        request.getfixturevalue("fragment_updater"),
        request.getfixturevalue("bibliography"),
        request.getfixturevalue("user"),
        request.getfixturevalue("fragment_repository"),
        request.getfixturevalue("parallel_line_injector"),
        request.getfixturevalue("changelog"),
        request.getfixturevalue("when"),
    )


def test_update_references(fragment_references_context):
    context = fragment_references_context
    fragment = FragmentFactory.build()
    number = fragment.number
    reference = ReferenceFactory.build()
    references = (reference,)
    updated_fragment = fragment.set_references(references)
    injected_fragment = updated_fragment.set_text(
        context.parallel_line_injector.inject_transliteration(updated_fragment.text)
    )
    context.when(context.bibliography).canonicalize_references(references).thenReturn(
        references
    )
    context.when(context.fragment_repository).query_by_museum_number(number).thenReturn(
        fragment
    ).thenReturn(updated_fragment)
    context.when(context.fragment_repository).update_field(
        "references", updated_fragment
    ).thenReturn()
    context.when(context.changelog).create(
        "fragments",
        context.user.profile,
        {"_id": str(number), **SCHEMA.dump(fragment)},
        {"_id": str(number), **SCHEMA.dump(updated_fragment)},
    ).thenReturn()

    result = context.fragment_updater.update_references(
        number, references, context.user
    )
    assert result == (injected_fragment, False)


def test_update_references_invalid(
    fragment_updater, bibliography, user, fragment_repository, when
):
    fragment = FragmentFactory.build()
    number = fragment.number
    reference = ReferenceFactory.build()
    references = (reference,)
    when(bibliography).canonicalize_references(references).thenRaise(DataError)
    (when(fragment_repository).query_by_museum_number(number).thenReturn(fragment))

    with pytest.raises(DataError):
        fragment_updater.update_references(number, references, user)
