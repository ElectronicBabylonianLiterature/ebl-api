from typing import Tuple, Mapping, Callable, Sequence

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.atf import Flag
from ebl.transliteration.domain.enclosure_tokens import Side, \
    DocumentOrientedGloss, BrokenAway, PerhapsBrokenAway, Erasure, \
    OmissionOrRemoval
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.sign_tokens import Divider, UnidentifiedSign, \
    UnclearSign
from ebl.transliteration.domain.tokens import Token, ValueToken, \
    LanguageShift, LineContinuation, UnknownNumberOfSigns, \
    Tabulation, CommentaryProtocol, Column, Variant
from ebl.transliteration.domain.word_tokens import Partial, ErasureState, \
    Word, LoneDeterminative, Joiner, InWordNewline

_factories: Mapping[str, Callable[[dict], Token]] = {
    'Token': lambda data: ValueToken(
        data['value']
    ),
    'Word': lambda data: Word(
        data['value'],
        Language[data['language']],
        data['normalized'],
        tuple(data['uniqueLemma']),
        ErasureState[data.get('erasure', ErasureState.NONE.name)],
        data.get('alignment'),
        parts=create_tokens(data.get('parts', []))
    ),
    'LanguageShift': lambda data: LanguageShift(
        data['value']
    ),
    'LoneDeterminative': lambda data: LoneDeterminative(
        data['value'],
        Language[data['language']],
        data['normalized'],
        tuple(data['uniqueLemma']),
        ErasureState[data.get('erasure', ErasureState.NONE.name)],
        data.get('alignment'),
        partial=Partial(*data['partial']),
        parts=create_tokens(data.get('parts', []))
    ),
    'DocumentOrientedGloss': lambda data: DocumentOrientedGloss(
        data['value']
    ),
    'BrokenAway': lambda data: BrokenAway(
        data['value']
    ),
    'PerhapsBrokenAway': lambda data: PerhapsBrokenAway(
        data['value']
    ),
    'OmissionOrRemoval': lambda data: OmissionOrRemoval(
        data['value']
    ),
    'LineContinuation': lambda data: LineContinuation(data['value']),
    'Erasure': lambda data: Erasure(data['value'],
                                    Side[data['side']]),
    'UnknownNumberOfSigns': lambda data: UnknownNumberOfSigns(),
    'Tabulation': lambda data: Tabulation(
        data['value']
    ),
    'CommentaryProtocol': lambda data: CommentaryProtocol(
        data['value']
    ),
    'Divider': lambda data: Divider(
        data['divider'],
        tuple(data['modifiers']),
        tuple(Flag(flag) for flag in data['flags'])
    ),
    'Column': lambda data: Column(data['number']),
    'Variant': lambda data: Variant(tuple(
        _factories[inner_token['type']](inner_token)
        for inner_token in data['tokens']
    )[:2]),
    'UnidentifiedSign': lambda data: UnidentifiedSign(
        tuple(Flag(flag) for flag in data['flags'])
    ),
    'UnclearSign': lambda data: UnclearSign(
        tuple(Flag(flag) for flag in data['flags'])
    ),
    'Joiner': lambda data: Joiner(atf.Joiner(data['value'])),
    'InWordNewline': lambda data: InWordNewline()
}


def create_token(data: dict) -> Token:
    return _factories[data['type']](data)


def create_tokens(tokens: Sequence[dict]) -> Tuple[Token, ...]:
    return tuple(map(create_token, tokens))
