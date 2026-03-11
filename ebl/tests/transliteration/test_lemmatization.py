from ebl.lemmatization.domain.lemmatization import Lemmatization, LemmatizationToken


def create_token(value, unique_lemma=None):
    return LemmatizationToken(value, () if unique_lemma is None else unique_lemma)


def create_lemmatized_token(value):
    return create_token(value, [value])


TOKENS = ((create_token("token"),),)


def test_equality():
    lemmatization = Lemmatization(TOKENS)
    similar = Lemmatization(TOKENS)
    different = Lemmatization(((create_token("another token"),),))

    assert lemmatization == similar
    assert hash(lemmatization) == hash(similar)
    assert lemmatization != different
    assert hash(lemmatization) != hash(different)


def test_tokens():
    lemmatization = Lemmatization(TOKENS)

    assert lemmatization.tokens == TOKENS
