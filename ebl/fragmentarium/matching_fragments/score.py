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
    if len(seq1) >= len(seq2):
        longer_seq = seq1
        shorter_seq = seq2
    else:
        longer_seq = seq2
        shorter_seq = seq1
    matching_subseq = []
    for i in range(1, len(longer_seq) + 1):
        if i >= len(shorter_seq):
            if longer_seq[i - len(shorter_seq) : i] == shorter_seq[-i:]:
                matching_subseq.append(shorter_seq[-i:])
        elif longer_seq[:i] == shorter_seq[-i:]:
            matching_subseq.append(shorter_seq[-i:])
    return matching_subseq


def weight_subsequence(seq_of_seq):
    weighting = []
    for seq in seq_of_seq:
        counter = 0
        for i in seq:
            if i == 0:
                counter = counter + 3
            elif i == 1:
                counter = counter + 1
            elif i == 2:
                counter = counter + 3
            elif i == 3:
                counter = counter + 6
            elif i == 4:
                counter = counter + 10
            elif i == 5:
                counter = counter + 3
            else:
                raise ValueError(f"{i} not a valiable ruling encoding")
            weighting.append(counter)
    return max(weighting)
