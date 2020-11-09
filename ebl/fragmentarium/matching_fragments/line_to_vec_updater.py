from typing import Sequence, Tuple

import  pandas as pd
import inspect

import textdistance
from IPython.core.display import display, HTML

from ebl.fragmentarium.domain.fragment import LineToVec
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain import text_line, dollar_line
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.line_number import LineNumber






def create_line_to_vec(lines: Sequence[Line]) -> Tuple[int]:
    line_to_vec = []
    for line in lines:
        if isinstance(line, text_line.TextLine):
            if isinstance(line.line_number, LineNumber):
                if line.line_number.has_prime:  # pyre-ignore[16]
                    line_to_vec.append(1)
            else:
                line_to_vec.append(0)
        elif isinstance(line, dollar_line.RulingDollarLine):
            if line.number == atf.Ruling.SINGLE:
                line_to_vec.append(2)
            elif line.number == atf.Ruling.DOUBLE:
                line_to_vec.append(3)
            elif line.number == atf.Ruling.TRIPLE:
                line_to_vec.append(4)
        elif isinstance(line, dollar_line.StateDollarLine) and line.extent == atf.Extent.END_OF:
                line_to_vec.append(5)
    return tuple(line_to_vec)


def calculate_distance(l1: Sequence[int], l2: Sequence[int],) -> float:
    print(l1)
    print(l2)
    x = textdistance.levenshtein.normalized_similarity(
        ''.join([str(x) for x in list(l1)]), ''.join([str(x) for x in list(l2)])
    )
    print(x)
    return x

def calculate_all_metrics(vec_1, vec_2):
    result = {}
    for distance in dir(textdistance):
        if not (distance in ["VERSION", "algorithms"] or distance.startswith("_") or not inspect.isclass(getattr(textdistance, distance))):
            result[distance] = getattr(textdistance, distance)().normalized_distance(vec_1, vec_2)
    return result

def metrics():
    metrics = []
    for distance in dir(textdistance):
        if not (distance in ["VERSION", "algorithms"] or distance.startswith("_") or not inspect.isclass(getattr(textdistance, distance))):
            metrics.append(distance)
    return metrics
"""
df = pd.read_excel("/home/yunus/PycharmProjects/ebl-api/ebl/fragmentarium/application/Line-Ruling-Sequences_2.xlsx")
for distance in dir(textdistance):
    if not (distance in ["VERSION", "algorithms"] or distance.startswith("_") or not inspect.isclass(getattr(textdistance, distance))):
        df[distance] = df.apply(lambda x: round(getattr(textdistance, distance)().normalized_distance(x["Fragment_1"], x["Fragment_2"]), 2), axis=1)

df.loc['mean'] = round(df.mean(), 2)
df.to_csv("df.csv")

df_new = pd.read_csv("/ebl/fragmentarium/application/df.csv")
df_random = pd.read_csv("/ebl/fragmentarium/matching_fragments/distances.tsv", sep=',', lineterminator='\n')
df_new.loc[30] = df_random.iloc[0]
df_new.to_csv("df_with_random.csv")



for distance in dir(textdistance):
    if distance[0].islower() and distance not in ["algorithms", "base", "compression_based", "edit_based", "find_ngrams", "libraries"]:
        print(distance)
        print(getattr(textdistance, distance).normalized_similarity("Fragment_1", "Fragment_2"))
        #print(getattr(textdistance, distance).normalized_similarity("Fragment_1", "Fragment_2"))


df.to_csv("df.csv")

"""
