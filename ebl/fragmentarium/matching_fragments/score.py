from ebl.fragmentarium.domain.fragment import LineToVecEncoding


def score_weighted(seq1, seq2):
    matching_seq = feed_compute_score(seq1, seq2)
    matching_seq = [seq for seq in matching_seq if list(filter(lambda x: x != 1, seq))]
    if len(matching_seq) and all(matching_seq):
        return weight_subsequence(matching_seq)
    else:
        return 0


def score(seq1, seq2):
    matching_seq = feed_compute_score(seq1, seq2)
    return max([len(x) for x in matching_seq]) if len(matching_seq) else 0


def feed_compute_score(seq1, seq2):
    return [*compute_score(seq1[::-1], seq2[::-1]), *compute_score(seq1, seq2)]


def compute_score(seq1, seq2):
    shorter_seq, longer_seq = sorted((seq1, seq2), key=len)
    matching_subseq = []
    for i in range(1, len(longer_seq) + 1):
        if i >= len(shorter_seq):
            if longer_seq[i - len(shorter_seq) : i] == shorter_seq[-i:]:
                matching_subseq.append(shorter_seq[-i:])
        elif longer_seq[:i] == shorter_seq[-i:]:
            matching_subseq.append(shorter_seq[-i:])
    return matching_subseq


LineToVecWeighting = {
    LineToVecEncoding.START: 2,
    LineToVecEncoding.TEXT_LINE: 0,
    LineToVecEncoding.SINGLE_RULING: 2,
    LineToVecEncoding.DOUBLE_RULING: 4,
    LineToVecEncoding.TRIPLE_RULING: 8,
    LineToVecEncoding.END: 2,
}


def weight_subsequence(seq_of_seq):
    weighting = {0: 3, 1: 1, 2: 3, 3: 6, 4: 10, 5: 3}
    return max(
        sum(elem)
        for elem in [[weighting[number] for number in seq] for seq in seq_of_seq]
    )
