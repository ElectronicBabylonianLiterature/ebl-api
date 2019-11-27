from ebl.transliteration.domain.lemmatization import Lemmatization


def create_token(value, unique_lemma=None):
    return {
        "value": value,
        "uniqueLemma": [] if unique_lemma is None else unique_lemma,
    }


def create_lemmatized_token(value):
    return create_token(value, [value])


TOKENS = [[create_token("token")]]


def test_equality():
    lemmatization = Lemmatization.from_list(TOKENS)
    similar = Lemmatization.from_list(TOKENS)
    different = Lemmatization.from_list([[create_token("another token")]])

    assert lemmatization == similar
    assert hash(lemmatization) == hash(similar)
    assert lemmatization != different
    assert hash(lemmatization) != hash(different)


def test_tokens():
    tokens = (tuple(),)
    lemmatization = Lemmatization(tokens)

    assert lemmatization.tokens == tokens
