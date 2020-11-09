from typing import Sequence

import pydash

seq1 = (1,2,1)
seq2 = (1,2,1)

def matching_subsequence(seq1, seq2):
    matching_subsequences = []
    try:
        for index, value in ((i,v) for i,v  in enumerate(seq1) if v != 1):
            if value in seq2:
                index2 = seq2.index(value)
                if all(s1 == s2 for s1, s2 in zip(seq1[index:], seq2[index2:])):
                    matching_subsequences.append(shortest_list_length(seq1[index:],  seq2[index2:]))
    except (StopIteration, ValueError):
        raise Exception("It looks like there are just text lines (1) in at least one of the sequences")
    return max(matching_subsequences) + 1 if matching_subsequences else 0



def shortest_list_length(seq1: Sequence, seq2: Sequence)-> int:
    x = len(seq1) if len(seq1) <= len(seq2) else len(seq2)
    return x

print(matching_subsequence(seq1, seq2))
print(matching_subsequence(seq2, seq1))




