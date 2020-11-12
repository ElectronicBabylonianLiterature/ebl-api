from typing import Sequence

import pydash

seq1 = (1,2,1)
seq2 = (1,2,1)

def matching_subseq(seq1, seq2):
    r1 = score(seq1, seq2)
    r2 = score(seq1[::-1], seq2[::-1])
    return max(r1, r2)

def matching_subseq_w(seq1, seq2):
    r1 = score_w(seq1, seq2)
    r2 = score_w(seq1[::-1], seq2[::-1])
    return max(r1, r2)

def score(seq1, seq2):
    if len(seq1) >= len(seq2):
        longer_seq = seq1
        shorter_seq = seq2
    else:
        longer_seq = seq2
        shorter_seq = seq1
    matching_subseq = []
    for i in range(1, len(longer_seq)+1):
        if i >= len(shorter_seq):
            if longer_seq[i - len(shorter_seq):i] == shorter_seq[-i:]:
                matching_subseq.append(shorter_seq[-i:])
        elif longer_seq[:i] == shorter_seq[-i:]:
            matching_subseq.append(shorter_seq[-i:])
    return max([len(x) for x in matching_subseq]) if len(matching_subseq) else 0

def score_w(seq1, seq2):
    if len(seq1) >= len(seq2):
        longer_seq = seq1
        shorter_seq = seq2
    else:
        longer_seq = seq2
        shorter_seq = seq1
    matching_subseq = []
    for i in range(1, len(longer_seq) + 1):
        if i >= len(shorter_seq):
            if longer_seq[i - len(shorter_seq):i] == shorter_seq[-i:]:
                matching_subseq.append(shorter_seq[-i:])
        elif longer_seq[:i] == shorter_seq[-i:]:
            matching_subseq.append(shorter_seq[-i:])
    matching_subseq = [seq for seq in matching_subseq if list(filter(lambda x: x != 1, seq))]
    if len(matching_subseq) and all(matching_subseq):
        return weight_subsequence(matching_subseq)
    else:
        return 0


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






