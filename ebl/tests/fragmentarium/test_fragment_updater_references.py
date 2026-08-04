import pytest

from ebl.errors import DataError
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.fragmentarium.fragment_updater_test_helpers import UpdaterContext


def test_update_references(
    fragment_updater, bibliography, updater_context: UpdaterContext
):
    fragment = FragmentFactory.build()
    number = fragment.number
    reference = ReferenceFactory.build()
    references = (reference,)
    updated_fragment = fragment.set_references(references)
    injected_fragment = updater_context.inject(updated_fragment)
    updater_context.when(bibliography).canonicalize_references(references).thenReturn(
        references
    )
    updater_context.expect_query(number, fragment, updated_fragment)
    updater_context.expect_update_field("references", updated_fragment)
    updater_context.expect_changelog(number, fragment, updated_fragment)

    result = fragment_updater.update_references(
        number, references, updater_context.user
    )
    assert result == (injected_fragment, False)


def test_update_references_invalid(
    fragment_updater, bibliography, updater_context: UpdaterContext
):
    fragment = FragmentFactory.build()
    number = fragment.number
    reference = ReferenceFactory.build()
    references = (reference,)
    updater_context.when(bibliography).canonicalize_references(references).thenRaise(
        DataError
    )
    updater_context.expect_query(number, fragment)

    with pytest.raises(DataError):
        fragment_updater.update_references(number, references, updater_context.user)
