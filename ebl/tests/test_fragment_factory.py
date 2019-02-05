def test_dict_serialization(fragment_factory, lemmatized_fragment):
    new_fragment = fragment_factory.create_from_dict(
        lemmatized_fragment.to_dict()
    )

    assert new_fragment == lemmatized_fragment
