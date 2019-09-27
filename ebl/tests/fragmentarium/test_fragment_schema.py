from ebl.fragmentarium.infrastructure.fragment_schema import FragmentSchema
from ebl.tests.factories.bibliography import ReferenceWithDocumentFactory
from ebl.tests.factories.fragment import FragmentFactory, \
    LemmatizedFragmentFactory
from ebl.users.domain.user import Guest

ANY_USER = Guest()


def test_create():
    lemmatized_fragment = LemmatizedFragmentFactory.build()
    new_fragment = FragmentSchema().load(lemmatized_fragment.to_dict())

    assert new_fragment == lemmatized_fragment


def test_create_with_dependencies(bibliography):
    reference = ReferenceWithDocumentFactory.build()
    fragment = FragmentFactory.build(references=(reference, ))
    bibliography.create(reference.document, ANY_USER)

    new_fragment = FragmentSchema().load(fragment.to_dict(True))

    assert new_fragment == fragment
