

import pyalign
import numpy as np
from alignment.sequence import Sequence
from alignment.vocabulary import Vocabulary

v = Vocabulary()
a1 = v.encodeSequence(Sequence(["asdasd", "asdasdasdasd", "ABZ76"]))
alignment = pyalign.global_alignment(np.array([1., 2.], dtype=np.int32), np.array([1., 2.], np.int32), gap_cost=0, eq=1, ne=-1)
print(alignment.score)