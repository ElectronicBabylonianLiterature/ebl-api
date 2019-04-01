import attr


def test_create(fragment_factory, lemmatized_fragment):
    new_fragment = fragment_factory.create(
        lemmatized_fragment.to_dict()
    )

    assert new_fragment == lemmatized_fragment


def test_create_with_dependencies(fragment_factory,
                                  fragment,
                                  reference_with_document,
                                  bibliography,
                                  bibliography_entry,
                                  user):
    # pylint: disable=R0913
    bibliography.create(bibliography_entry, user)
    expected = attr.evolve(fragment, references=(reference_with_document, ))

    new_fragment = fragment_factory.create_denormalized(
        expected.to_dict(False)
    )

    assert new_fragment == expected
