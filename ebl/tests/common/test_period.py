from ebl.common.domain.period import Period


def test_mapping():
    for period in Period:
        assert Period.from_name(period.long_name) == period
