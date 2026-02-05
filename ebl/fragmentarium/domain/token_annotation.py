from typing import Dict, NewType

from ebl.lemmatization.domain.lemmatization import Lemma

TokenIndex = NewType("TokenIndex", int)
LineIndex = NewType("LineIndex", int)

LineLemmaAnnotation = NewType("LineLemmaAnnotation", Dict[TokenIndex, Lemma])
TextLemmaAnnotation = NewType(
    "TextLemmaAnnotation", Dict[LineIndex, LineLemmaAnnotation]
)
LemmaSuggestions = NewType("LemmaSuggestions", Dict[str, Lemma])
