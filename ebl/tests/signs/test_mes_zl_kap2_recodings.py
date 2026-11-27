from ebl.signs.mes_zl_kap2_recodings import (
    KAP2_RECODINGS,
    Kap2Recoding,
    recode_kap2,
)

AMAS = "\U001000d4"


def test_recodes_placeholders_everywhere() -> None:
    recoded, _ = recode_kap2(
        {
            "1": "Jahre ( 𒉽, ⟦098a⟧ usw.)",
            "92": "Zu den Datierungen 𒉽 , ⟦098a⟧ usw.",
            "98": "⟦098a⟧ siehe oben n1.",
        }
    )
    assert recoded == {
        "1": "Jahre ( 𒉽, \U001000cf usw.)",
        "92": "Zu den Datierungen 𒉽 , \U001000cf usw.",
        "98": "\U001000cf siehe oben n1.",
    }


def test_amas_replaces_dag_and_placeholder() -> None:
    recoded, _ = recode_kap2(
        {"460": "Man kann 𒎎⟦688a⟧ entweder", "464": "𒉺 𒁖⟦688a⟧\t**— PA-AMAŠ"}
    )
    assert recoded == {
        "460": f"Man kann {AMAS} entweder",
        "464": f"𒉺 {AMAS}\t**— PA-AMAŠ",
    }


def test_sequences_only_in_their_entries() -> None:
    recoded, _ = recode_kap2({"464": "𒉺𒀠\t**— ŠAB", "1": "𒉺𒀠 = pa-al"})
    assert recoded == {"464": "\U001000db\t**— ŠAB", "1": "𒉺𒀠 = pa-al"}


def test_sa6_in_alam_keeps_the_second_sign() -> None:
    entries = {
        "564": "𒅊 𒋺 𒊷𒈿 — SIG₇-KÍD-ALAM\n𒅊 𒊷𒈿 — SIG₇-ALAM",
        "766": "𒇇 𒊷𒈿 — U₈-ALAM",
    }
    recoded, _ = recode_kap2(entries)
    assert recoded["766"] == "𒇇 \U001000d2𒈿 — U₈-ALAM"
    assert recoded["564"].count("\U001000d2𒈿") == 2


def test_unexpected_count_is_reported_and_not_applied() -> None:
    rule = Kap2Recoding("x", "⟦x⟧", "\U001000cf", 2)
    recoded, [report] = recode_kap2({"1": "⟦x⟧"}, [rule])
    assert recoded == {"1": "⟦x⟧"}
    assert report.found == 1
    assert not report.is_expected


def test_is_idempotent() -> None:
    once, _ = recode_kap2({"1": "⟦098a⟧ ⟦098a⟧ ⟦098a⟧"})
    twice, reports = recode_kap2(once)
    assert twice == once
    assert all(report.found == 0 and report.is_expected for report in reports)


def test_every_rule_changes_its_passage() -> None:
    for rule in KAP2_RECODINGS:
        assert rule.old != rule.new
        assert rule.expected > 0
