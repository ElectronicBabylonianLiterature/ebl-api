import pytest  # pyre-ignore[21]

from ebl.fragmentarium.application.matches.create_line_to_vec import (
    create_line_to_vec,
    LineToVecEncoding,
    split_lines,
)
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.transliteration.domain.lark_parser import parse_atf_lark


@pytest.mark.parametrize(
    "atf, expected",
    [
        [
            "1'-2'. [x x x x x x x x] x na-aš₂-al;-[b]a pu-ti-ka",
            (LineToVecEncoding.from_list([1, 1]),),
        ],
        [
            "1-2. [x x x x x x x x] x na-aš₂-al;-[b]a pu-ti-ka",
            (LineToVecEncoding.from_list([0, 1, 1]),),
        ],
        [
            "1-2. [x x x x x x x x] x na-aš₂-al;-[b]a pu-ti-ka\n1'. [...]",
            (LineToVecEncoding.from_list([0, 1, 1]), LineToVecEncoding.from_list([1])),
        ],
        [
            "1. x [...]\n@colophon\n2. x [...]",
            (LineToVecEncoding.from_list([0, 1, 1]),),
        ],
        ["1'. x [...]\n@colophon\n2'. x [...]", (LineToVecEncoding.from_list([1, 1]),)],
        [
            "1. x [...]\n@column 1\n2. x [...]",
            (LineToVecEncoding.from_list([0, 1, 1]),),
        ],
        ["1'. x [...]\n@obverse\n2'. x [...]", (LineToVecEncoding.from_list([1, 1]),)],
        [
            "1'. x [...]\n@obverse\n1'. x [...]",
            (LineToVecEncoding.from_list([1]), LineToVecEncoding.from_list([1])),
        ],
        [
            "1. x [...]\n@obverse\n1. x [...]",
            (LineToVecEncoding.from_list([0, 1]), LineToVecEncoding.from_list([0, 1])),
        ],
        [
            "@obverse\n1'. x [...]\n@reverse\n1'. x [...]\n2'. x [...]\n@edge\n1'. x [...]",
            (
                LineToVecEncoding.from_list([1]),
                LineToVecEncoding.from_list([1, 1]),
                LineToVecEncoding.from_list([1]),
            ),
        ],
        [
            "1. x [...]\n2. x [...]\n$ end of side\n1'. x [...]",
            (
                LineToVecEncoding.from_list([0, 1, 1, 5]),
                LineToVecEncoding.from_list([1]),
            ),
        ],
[
            """@reverse
1'. %sux [...] & %sb [ma]-am#-ma#-an a-a i#-x-[x]
$ single ruling
2'. %sux [ša₃] gidru#-[ka] & %sb a-na ŠA₃ ha-aṭ-ṭi
3'. %sux [i₃] si-[x (x)] & %sb šam-nu ša-pi-ik-ma
4'. %sux [lu₂ n]a-me nu-un-z[u] & %sb ma-am-man ul i-di
#note: Proverb Collection 1.104, etc.
$ single ruling
5'. %sux [šum₂-m]a-ab lugal-la-ke₄ & %sb na-da-nu ša₂ LUGAL
6'. %sux [dug₃-g]a sagi(|ŠU.SILA₃.GABA|)-ke₄ & %sb ṭu₂-ub-bu ša₂ ša₂-qi₂-i
#note: Proverb Collection 3.86, etc., original proverb has two commands
$ single ruling
7'. %sux [šu]m₂-ma-ab [lug]al-la-ke₄ &
8'. %sux [s]ag₉-ga agrig-a-ke₄ & %sb dum-mu-qu ša₂ a-ba-rak-ku
$ single ruling
9'. %sux nam-gu₅-li nig₂ ud diš-kam@v & %sb ib-ru-tu₄ ša u₄-ma-ak-k[al]
10'. %sux nam-gi₄-me-a-aš & %sb ki-na-tu-tu
11'. %sux nig₂ ud da-ri₂-kam₂ & %sb ša₂ da-ra-a-t[i]
#note: Proverb Collection 3.17
$ single ruling
12'. %sux du₁₄-da %sb ṣa-al-tu
13'. %sux ki nam-gi₄-me-a-aš-ke₄ & %sb a-šar ki-na-tu-ti
14'. %sux eme-sig gu₇-gu₇ & %sb kar-ṣi a-ka-li
15'. %sux ki nam-luh-še₃ i₃-gal₂ & %sb a-šar pa-ši-šu-ti ib-ba₂-aš-ši
#note: Proverb Collection 3.18, proverb cited @i{CAD} P, 255 @sux{nam-luh} or @sux{nam-sukkal? nam-<kisal>-luh?} Alster “place of purification”, OB variant @sux{nam-a-luh}.
$ single ruling
16'. %sux gir₅ iri kur₂-ra-am₃ & %sb u-bar-ru ina URU ša₂-nim-ma
17'. %sux sag-ga₂-am₃ & %sb re-e-šu₂
$ single ruling
18'. &2 %sux {na₄}kin₂ nu-un-uri₃-me-en
$ single ruling
19'. &2 %sux nam-dub-sar-ra ama gu₃ de₂-ke₄-e-ne a-a um-me-a-ke₄-eš
#note: Incipit to Examination Text D, see @bib{RN1449@126}.
@colophon
20'. &2 KUR {m}AN.ŠAR₂-DU₃-A MAN ŠU₂ MAN {kur}AN.ŠA[R₂]{k[i}]
$ end of side""",
            (
                LineToVecEncoding.from_list([1,2,1,1,1,2,1,1,2,1,1,2,1,1,1,2,1,1,1,1,2,1,1,2,1,2,1,1,5]),
            ),
        ],
    ],
)
def test_create_line_to_vec_from_atf(atf, expected, transliteration_factory):
    lines = parse_atf_lark(atf).lines
    assert create_line_to_vec(lines) == expected


@pytest.mark.parametrize(
    "atf, expected",
    [
        ["1'. x [...]\n@colophon\n2'. x [...]", [3, 3]],
        ["1'. x [...]\n@column 2\n1'. x [...]", [2, 2]],
        ["1'. x [...]\n@obverse\n2'. x [...]", [3, 3]],
        ["1'. x [...]\n@obverse\n1'. x [...]", [2, 2]],
        ["1. x [...]\n2. x [...]\n$ end of side\n1'. x [...]", [3, 3]],
    ],
)
def test_split_lines(atf, expected):
    lines = parse_atf_lark(atf).lines
    splitted_lines = tuple(
        [line for line in [lines[: expected[0]], lines[expected[1] :]] if len(line)]
    )
    assert split_lines(lines) == splitted_lines


def test_split_multiple_lines():
    lines = parse_atf_lark(
        "@obverse\n1'. x [...]\n@reverse\n1'. x [...]\n2'. x [...]\n@edge\n1'. x [...]"
    ).lines
    splitted_lines = tuple([lines[:3], lines[3:6], lines[6:]])
    assert split_lines(lines) == splitted_lines


def test_create_line_to_vec():
    fragment = TransliteratedFragmentFactory()
    line_to_vec = create_line_to_vec(fragment.text.lines)
    assert fragment.line_to_vec == line_to_vec


def test_line_to_vec_encoding_from_list():
    assert (
        LineToVecEncoding(0),
        LineToVecEncoding(1),
        LineToVecEncoding(2),
        LineToVecEncoding(3),
        LineToVecEncoding(4),
        LineToVecEncoding(5),
    ) == LineToVecEncoding.from_list([0, 1, 2, 3, 4, 5])
