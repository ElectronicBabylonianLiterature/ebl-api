import math
import random
from typing import Callable, Iterable, List, Sequence

import attr
import pydash  # pyre-ignore
from joblib import Parallel, delayed  # pyre-ignore
from tqdm import tqdm  # pyre-ignore

from ebl.app import create_context
from ebl.context import Context
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.matching_fragments.line_to_vec_updater import \
    calculate_all_metrics, create_line_to_vec
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.fragmentarium.matching_fragments.score import matching_subsequence
from ebl.transliteration.infrastructure.menoizing_sign_repository import (
    MemoizingSignRepository,
)

from dotenv import load_dotenv
load_dotenv()


def create_context_() -> Context:
    context = create_context()
    context = attr.evolve(
        context, sign_repository=MemoizingSignRepository(context.sign_repository)
    )
    return context


def load_fragment():
    fragmentId = "K.2354"
    context = create_context()
    fragment_repository = context.fragment_repository
    x = fragment_repository.query_by_museum_number(MuseumNumber.of(fragmentId))


load_fragment()
