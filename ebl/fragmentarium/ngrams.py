def to_ngrams(signs):
    return {ngram for ngram_row in [_row_to_ngrams(row) for row in signs] for ngram in ngram_row}


def _row_to_ngrams(row):
    min_n = 3
    length = len(row)
    ns = range(min_n, max(length, min_n) + 1)
    return [
        ''.join(row[index:index + n])
        for n in ns
        for index in range(0, max(0, length - n) + 1)
    ]
