from ebl.dictionary.infrastructure.akkadian_sort import akkadian_sort_key


def test_akkadian_sort_orders_words_with_roman_suffixes():
    test_words = [
        "šarru I",
        "Šarru II",
        "abālu I",
        "Abālu II",
        "ṣābū I",
        "zāru I",
        "part1 part2 IX",
        "part1 part2 V",
        "part1 part2 IV",
        "part1 part2 III",
        "part1 part2 VI",
        "part1 part2 II",
        "part1 part2 I",
        "bītu I",
        "Bītu I",
        "akalūtu I",
        "akālu I",
        "akalu I",
    ]

    expected = [
        "Abālu II",
        "abālu I",
        "akalu I",
        "akālu I",
        "akalūtu I",
        "Bītu I",
        "bītu I",
        "part1 part2 I",
        "part1 part2 II",
        "part1 part2 III",
        "part1 part2 IV",
        "part1 part2 V",
        "part1 part2 VI",
        "part1 part2 IX",
        "ṣābū I",
        "Šarru II",
        "šarru I",
        "zāru I",
    ]

    assert sorted(test_words, key=akkadian_sort_key) == expected
