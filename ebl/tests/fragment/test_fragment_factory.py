from ebl.tests.factories.fragment import FragmentFactory


def test_create(fragment_factory, lemmatized_fragment):
    new_fragment = fragment_factory.create(
        lemmatized_fragment.to_dict()
    )

    assert new_fragment == lemmatized_fragment


def test_create_with_dependencies(fragment_factory,
                                  reference_with_document,
                                  bibliography,
                                  bibliography_entry,
                                  user):
    fragment = FragmentFactory.build(references=(reference_with_document, ))
    bibliography.create(bibliography_entry, user)

    new_fragment = fragment_factory.create_denormalized(
        fragment.to_dict(False)
    )

    assert new_fragment == fragment
