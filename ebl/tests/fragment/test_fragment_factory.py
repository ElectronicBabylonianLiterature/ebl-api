from ebl.auth0 import Guest
from ebl.tests.factories.bibliography import ReferenceWithDocumentFactory
from ebl.tests.factories.fragment import FragmentFactory, \
    LemmatizedFragmentFactory

ANY_USER = Guest()


def test_create(fragment_factory):
    lemmatized_fragment = LemmatizedFragmentFactory.build()
    new_fragment = fragment_factory.create(
        lemmatized_fragment.to_dict()
    )

    assert new_fragment == lemmatized_fragment


def test_create_with_dependencies(fragment_factory, bibliography):
    reference = ReferenceWithDocumentFactory.build()
    fragment = FragmentFactory.build(references=(
        reference,
    ))
    bibliography.create(reference.document, ANY_USER)

    new_fragment = fragment_factory.create_denormalized(
        fragment.to_dict(False)
    )

    assert new_fragment == fragment
