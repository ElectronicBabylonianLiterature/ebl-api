import sys

from tqdm import tqdm

from ebl.transliteration.domain.lark_parser import parse_atf_lark

ATF = """@obverse
1. %es [uru₂-a bu]r₂-ra?#-[ah tur-ra-ta u₃-li-li še am-ša₄]
2. ($___$) [ina?] URU# re-bit [ṣe-eh-ra ina lal-la-ra-ti i]-dam#-mu#-u[m]
3. %es [t]ur-ra-ta uru₂-a b[ur₂?-ra-ah tur-ra-ta u₃-li-li še] am₃#-ša₄
4. %es [t]e-e-am₃ e₂ l[il₂-la₂ ba-si]-si-ga-t[a]
5. ($___$) min₃-su E₂ za-[qi₂-qi₂ ša₂ uš-qa]-am-ma-m[u]
6. %es [t]e-e-am₃ uru₂ lil₂-la₂# [ba-gi₄]-gi₄-da-t[a]
7. ($___$) [m]in₃-su ša₂ URU-ša₂ [ana za-qi₂-q]i₂ i-tu-r[u]
8. %es e₂#-gu₁₀ i₃-si-in{ki}-na & [bulug] an ki-[gu₁₀]
9. ($___$) [b]i-ti MIN & [pu-lu]-uk# AN-e u KI-[ti₃]
10. %es [am]a₅-gu₁₀ e₂-gal-mah & an#-ne₂ mar-ra-[gu₁₀]
11. ($___$) [m]aš-ta-ki E₂ MIN & ša₂ {d}a-nim iš-ru-[kam]
12. %es e₂#-gu₁₀ aš-te & e₂ la₇-ra₃-ak{ki}-[gu₁₀]
13. ($___$) E₂ ŠU-ma & E₂ la-[rak]
14. %es [la₇-r]a₃-ak{ki} uru₂ umun-na# & ba-ab-ze₂-e[g₃-ga₂-gu₁₀]
15. ($___$) [l]a-ra[k URU] ša₂ be-lu₄ id-[di-na?]
16. %es [sig]-še₃# [gul-la-gu₁₀] & nim-še₃ bu-[ra-gu₁₀]
17. ($___$) [šap-liš it-tan-qar] e-liš it-[tan-sah]
18. %es [balag-di erim₃-ma-gu₁₀ & u]r-re#-eš ma-a[l-la-gu₁₀]
19. ($___$) [ina ṣer-hi i-šit-ti ana nak]-ri i[t-taš-kan]
20. %es [bad₃-si-bi ba-ra-gul tu{mušen}-bi am₃-nigin-e]
21. ($___$) [(...) it-ta-ʾ-ba-tu su-um-ma-tu-šu₂ iṣ-ṣa-nu-ud-da]
22. %es [{mu}ka₂-na-bi ba-ra-si-il ki u₆-di la-ba-an-tuku]
23. ($___$) [(...) iš-ta-al-la-at a-šar tab-ri-ti ul i-ši]
24. %es [{mu}ur₃-bi mu-lu u₃-mun tu₁₀-ba-gin₇ u₄-de₃ ba-ku-ku-uš]
25. ($___$) [... ha-tu-u₂ ṣe-e-ti₃/ti it-tan-du-u₂]
26. %es še-e[b sag zi-ga ama er₂-ra-gin₇ er₂-ra eg₃-ge₂₆-tuš?/zal?]
27. ($___$) li-b[it-tu ... ki-ma um-mi bi-ki-ti ...]
28. %es gi-sal-la-bi siki# [ze₂-a-gin₇ ki ag₂/am₃-da-bi-us₂]
29. ($___$) gi-sal-lu-šu ki-ma šar#-ti# ba#-qim#-ti# e[r?-ṣe?-tu₄? it/im-ta-lu-u₂]
#note: cf. SBH 36: 29
30. %es gi guruš₃{+ru-uš}-bi mu-lu ša₃ gig-ga-gin₇ šu ma-al#-[la gur₄-gur₄-re]
31. ($___$) hur-du-šu₂ ki-ma ša₂ ki-iṣ lib₃-bi it-ta-na-ra[m ...]
32. %es bur₂-ra-ah-bi su-din{mušen} dal-la-gin₇ du₆/habrud-da al-g[ir₅-gir₅-re]
33. %es za₃ du₈-bi mu-lu a-tu₅-a-gin₇ & šu ur₃-ra ba-[ni-ib₂-ri]
34. %es {giš#}ig a₂ si-bi & bar-bi [ak-a-ab]
35. %es {giš#}suhub₃ {giš}sag-kul-bi & še am₃-mu-[ni-ib₂-ša₄]
36. %es [{mu}]gi ba-ra me-a & lil₂-la₂ [am₃-ma-ni-in-ku₄]
37. %es [e₂] uru₂ sag-ga₂-gu₁₀ & lil₂#-[la₂ <(am₃-ma-ni-in-ku₄)>]
38. %es [še-eb i₃-si-in{ki}-na-gu₁₀ lil₂-la₂ <(am₃-ma-ni-in-ku₄)>]
39. %es [e₂-gal-mah-a-gu₁₀ & lil₂-la₂ <(am₃-ma-ni-in-ku₄)>]
40. %es [e₂-rab-ri-ri-a-gu₁₀ & lil₂-la₂ <(am₃-ma-ni-in-ku₄)>]
41. %es [{giš?}tir? ku₃-ga-gu₁₀ & lil₂-la₂ <(am₃-ma-ni-in-ku₄)>]
42. %es [... x mušen-e & gud₃ im-ma-an-us₂-sa]
43. %es [... ab x & lib ba-an-mar-ra]
44. %es [... x x e-lum-e & na-ag₂-hul-hul?-a?#-še₃]
45. %es [umun-e] {d#}mu-[ul-lil₂-le lil₂-la₂-da (x) i₃?-ku₄?-ku₄?]
46. ($___$) be#-lu {d#}[MIN ana za-qi₂-qi₂ u₂-tir-ru]
47. %es [mu]-lu ka-n[ag-da ba-an-da-gur-ra lil₂-la₂-da <(...)>]
48. ($___$) ša# ma-a-tu₂ [is-ki-pu ana za-qi₂-qi₂]
49. %es [sag]-gig-ga-na# [ba-an-da-sal-la lil₂-la₂-da <(...)>]
50. %es [x b]a-an-tar-[tar buru₅{mušen} mu-da-an-dal-dal]
51. %es [uru₂]-gu₁₀ ag₂-g[ig-ga ba-ni-in- ...]
52. %es [umun]-e# unu₂ mah-a# [šu pe-el-la₂ ba-ab-d]u₁₁?
53. %es [e₂]-ga₂ im-ta-e₃#-[e bar-ta i₃-dab₅?-dab₅?-b]e₂?
54. %es [e₂]-ga₂ e₂-z[i-da šu pe-el-la₂ ba-ab-d]u₁₁
55. %es [{d}m]u-ul-lil₂-la₂ u[ru₂-gu₁₀ uru₂ zi-da a-še-er ma-ni?-in?-ma-a]l
56. %es [e₂-š]a₃-hul₂-la m[a-du₃-a-gu₁₀ a-še-er-ra x x x] x
57. %es [e₂] mu#-tin ma-r[a-de₂-a-gu₁₀ a-še-er-ra x x x (x) d]e₂?
58. %es [e₂ a]g₂-gu₇-a ba-[zi-ga ... z]i
59. %es [{giš}ma₂]-gur₈ ag₂-nidba# [...]-gur₃
60. %es [i₇-d]e₃ a-hul₂-la t[um₂-tum₂-mu a-hul x x] -de₂-e
61. %es [egi₂-r]e uru₂ ša₃-ab-b[a uru₂-ni x x (x x)] ba#-gul
62. %es [gašan-me-e]n uru₂ bar-r[a uru₂ x x (x x)] ba-hul
63. %es [šul-hi]-gu₁₀?# ba#-gul# [...] ba-ab-bar₃
64. %es [erim₃-ma-gu₁₀ ba-gul ug₃-bi] ba-tu₁₀-be₂-eš
65. %es [gašan-me-en i₃-id-di-in & u₃] nu#-ku-ku-me-en
66. %es [a₂ kuš₂-u₃-bi] & u₂ nu-gu₇-e
67. %es [a₂ kuš₂]-u₃#-bi# x & a nu-nag-e
$ single ruling
68. %es [mu-lu] u₆#-di & [e]-lum m[u-lu] u₆#-di
69. %es [e-lum] mu-lu u₆-di & i-bi₂-zu nu-kuš₂-u₃
70. %es [umun] kur-kur-ra# & mu-lu <(u₆-di i-bi₂-zu nu-kuš₂-u₃)>
71. %es [umun] du₁₁#-ga# zi-da & mu-lu <(u₆-di i-bi₂-zu nu-kuš₂-u₃)>
72. %es {d}mu-ul-lil₂ a-a ka-nag-ga₂ & mu-lu <(u₆-di i-bi₂-zu nu-kuš₂-u₃)>
73. %es sipa sag-gig₂-ga & mu-lu <(u₆-di i-bi₂-zu nu-kuš₂-u₃)>
74. %es i-bi₂ du₈ ni₂-te-en-na & mu-lu <(u₆-di i-bi₂-zu nu-kuš₂-u₃)>
75. %es am erin₂-na di-di & mu-lu <(u₆-di i-bi₂-zu nu-kuš₂-u₃)>
76. %es u₃ lul-la ku-ku & mu-lu <(u₆-di i-bi₂-zu nu-kuš₂-u₃)>
77. %es umun {d}am-an-ki# & mu-lu <(u₆-di i-bi₂-zu nu-kuš₂-u₃)>
78. %es ur-sag {d}asar-lu₂#-hi & mu-lu <(u₆-di i-bi₂-zu nu-kuš₂-u₃)>
79. %es umun {d}+en-bi-lu-lu & mu-lu <(u₆-di i-bi₂-zu nu-kuš₂-u₃)>
80. %es ur-sag {d}mu-ze₂-eb-ba-sa₄-a & mu-lu <(u₆-di i-bi₂-zu nu-kuš₂-u₃)>
81. %es umun {d}di-ku₅-mah-am₃ & mu#-lu# <(u₆-di i-bi₂-zu nu-kuš₂-u₃)>
82. %es ur-sag {d}utu-u₁₈-lu & mu-lu <(u₆-di i-bi₂-zu nu-kuš₂-u₃)>
83. %es umun {d}uraš-a-ra & mu-lu <(u₆-di i-bi₂-zu nu-kuš₂-u₃)>
84. %es i-bi₂-zu u₆-di-zu & nu-kuš₂-u₃
85. %es gu₂-zu ki#-ma#-[al-l]a & nu-gi₄-gi₄
86. %es ša₃#-zu# [bal-bal] & en₃-še₃ i₃-kuš₂-u₃
$ end of side

@reverse
1. %es u₈ sila₄ zi-da & kur₂-re ba-an-ze₂-eg₃
2. %es uz₃ maš₂ zi-da & kur₂-re <(ba-an-ze₂-eg₃)>
3. %es ag₂-tuku-da ag₂-ga₂-ni & mu-un-e-til
4. %es {d}mu-ul-lil₂-še₃ gal-gal-la sed-de₃ ba-an-gam i-bi₂-zu nu-kuš₂-u₃
$ single ruling
5. %es dilmun{ki} nigin-na & uru₂-zu u₆ ga₂-e-de₃
6. ($___$) kab-tu₄ : {d}+en-lil₂ na-as-hi-ram-ma & ana URU-ka tu-ur : URU-ka hi-iṭ-ṭi
7. %es alim-ma dilmun{ki} nigin-na & uru₂-zu <(u₆ ga₂-e-de₃)>
8. %es umun kur-kur-ra & nigin-na <(uru₂-zu u₆ ga₂-e-de₃)>
9. %es umun du₁₁-ga zi-da & nigin-na <(uru₂-zu u₆ ga₂-e-de₃)>
10. %es {d}mu-ul-lil₂ a-a ka-nag-ga₂ & nigin-na <(uru₂-zu u₆ ga₂-e-de₃)>
11. %es sipa sag-gig₂-ga & nigin-na <(uru₂-zu u₆ ga₂-e-de₃)>
12. %es i#-bi₂# du₈ ni₂-te-en-na & nigin-na <(uru₂-zu u₆ ga₂-e-de₃)>
13. %es [am erin₂]-na di-di & nigin-na <(uru₂-zu u₆ ga₂-e-de₃)>
14. %es [u₃] lul-la# ku-ku & nigin-na <(uru₂-zu u₆ ga₂-e-de₃)>
15. %es [umun] {d}am-an-ki & nigin-na <(uru₂-zu u₆ ga₂-e-de₃)>
16. %es ur-sag {d}asar-lu₂-hi & nigin-na <(uru₂-zu u₆ ga₂-e-de₃)>
17. %es umun {d}+en-bi-lu-lu & nigin-na <(uru₂-zu u₆ ga₂-e-de₃)>
18. %es [u]r-sag {d}mu-ze₂-eb-ba-sa₄-a & nigin-na <(uru₂-zu u₆ ga₂-e-de₃)>
19. %es [umun] {d}di-ku₅-mah-a & nigin-na <(uru₂-zu u₆ ga₂-e-de₃)>
20. %es [u]r-sag {d}utu-u₁₈-lu & nigin-na <(uru₂-zu u₆ ga₂-e-de₃)>
21. %es [umun] {d}uraš-a-ra & nigin-na <(uru₂-zu u₆ ga₂-e-de₃)>
22. %es [ur]u₂-zu nibru{ki}-ta & nigin-na <(uru₂-zu u₆ ga₂-e-de₃)>
23. %es [še-e]b e₂-kur-ra-ta & ki-ur₃ e₂-nam-ti-la
24. %es [še-e]b zimbir{ki}-ta & nigin-na <(uru₂-zu u₆ ga₂-e-de₃)>
25. %es [e]š₃ e₂-babbar-ra & e₂ di-ku₅-kalam-ma
26. %es [še-e]b tin-tir{ki}-ta & nigin-na <(uru₂-zu u₆ ga₂-e-de₃)>
27. %es [še-e]b e₂-sag-il₂-la & eš₃ e₂-tur₃-kalam-ma
28. %es [še-e]b bad₃-si-ab-ba{ki}-ta & nigin-na <(uru₂-zu u₆ ga₂-e-de₃)>
29. %es [še-e]b e₂-zi-da-ta & eš₃ e₂-mah-ti-la
30. %es [še-e]b e₂-te-me-an-ki & eš₃ e₂-dara₃-an-na
31. %es [še-e]b i₃-si-in{ki}-na-ta & nigin-na <(uru₂-zu u₆ ga₂-e-de₃)>
32. %es [še-eb] e₂-gal-mah & eš₃ e₂-rab-ri-ri
33. %es [uru₂] a du₁₁-ga & a gi₄-a-za
34. ($___$) [a-l]u₄ ša₂ nak-ru₃ u₂-ša₂-nu-u : a-hu-lap tu-ur-šu₂
35. %es nibru{ki} a du₁₁-ga & a-ta mar-ra-za
36. ($___$) ša₂ nak-ru u ana me-e sa-lu-u
37. %es uru₂ a du₁₁-ga & a gi₄-a-za
38. %es zimbir{ki} a du₁₁-ga & a-ta <(mar-ra-za)>
39. %es uru₂ a du₁₁-ga & a gi₄-<(a-za)>
40. %es tin-tir{ki} a du₁₁-ga & a-ta <(mar-ra-za)>
41. %es uru₂ a du₁₁-ga & a gi₄-<(a-za)>
42. %es i₃-si-in#{ki}-na a du₁₁-ga & a-ta <(mar-ra-za)>
43. %es uru₂ še ku₅-da & ki la₂-la₂-a-zu
44. %es ($___$) a-lu₄ ša₂ še-um ip-par-su-šu₂ & uṭ-ṭe-tu₄ iš-šaq-lu-šu
45. %es eg₃-gu₇ nu-gu₇-e & u₄ zal-tal-la-ri
46. ($___$) ak-ki-lu ina la a-ka-li & uš-tab-ru-u
47. %es dam tur-ra-ke₄ & dam-gu₁₀ mu-ni-ib₂-be₂
48. ($___$) ša₂ mu-us-sa₃ ṣe-eh-ru & mu-ti-ma i-qab-bi
49. %es dumu tur-ra-ke₄ & dumu-gu₁₀ mu-<(ni-ib₂-be₂)>
50. %es ki-sikil-gu₁₀ & šeš-gu₁₀ mu-<(ni-ib₂-be₂)>
51. ($___$) ar-da-tu₄ & a-hi-mi <(i-qab-bi)>
52. %es uru₂ ama-gan-gu₁₀ & dumu-gu₁₀ mu-<(ni-ib₂-be₂)>
53. ($___$) ina a-li um-mu a-lit-tu & ma-ri-mi <(i-qab-bi)>
54. %es dumu ban₃-da & a-a-gu₁₀ mu-<(ni-ib₂-be₂)>
55. ($___$) mar-tu₄ ṣe-her-tu₄ & a-bi-mi <(i-qab-bi)>
56. %es e-sir₂-ra gub-ba & mu-un-sar-re-e-NE
57. ($___$) ša₂ ina su-qi₂ iz-za-az-zu & uš-tah-mi-ṭu₂
58. %es tur-e al-e₃ & mah-e <<e>> al-e₃
59. ($___$) ṣe-eh-ru i-mah-hi & ra-bu-u₂ i-mah-hi
60. %es [ni]bru{ki} tur-e al-e₃ & mah-<(e al-e₃)>
61. %es [tin]-tir{ki} tur-e al-e₃ & mah-<(e al-e₃)>
62. %es [i₃-si-i]n{ki}-na tur-e al-e₃ & mah-<(e al-e₃)>
63. %es [sal-la-b]i & ur-re an-da-ab-la₂
64. ($___$) [qal-l]a-šu kal-bu uš-qa!#-lil : & na-ak-ru it-ta-ši
65. %es [sag₂-b]i & mu-bar-ra an-da-ab-la₂
66. ($___$) [sa-ap]-hu!(RI)-us-su & bar-ba-ru u₂-šaq-lil
67. %es [ki e-n]e-di & lil₂-la₂-am₃ e-si
68. ($___$) [me/me₂-lul]-ta-šu & zi-qi₂-qam im-ta-la
69. %es [e-sir₂ l]a-la-bi & nu-gi₄-gi₄
70. ($___$) [su-u₂]-qu ša₂ la-la#-a# & [l]a aš₂-bu-u₂
$ single ruling
71. %es [egi₂-re e]gi₂-re gu₃-a & [uru₂ in-ga-am₃-me] u₃-li-li
72. [2]-u₂ nis-hu %es mu-tin nu-nus dim₂-m[a? %sb NU AL.TIL]
73. [k]i-ma la-bi-ri-šu₂ ša₃-ṭir₂-ma ba-[ri]
74. KUR {m}AN.ŠAR₂-DU₃-A MAN ŠU₂ MAN KUR AN.ŠAR₂{ki}
$ end of side"""


if __name__ == "__main__":
    iterations = 1
    if len(sys.argv) > 1:
        iterations = int(sys.argv[1])

    for _ in tqdm(range(iterations), desc=f"Parsing"):
        parse_atf_lark(ATF)
