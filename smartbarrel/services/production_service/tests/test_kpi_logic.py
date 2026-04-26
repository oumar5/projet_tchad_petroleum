def test_wor_computation():
    oil = 1000.0
    water = 1500.0
    wor = water / oil
    assert wor == 1.5


def test_period_mapping():
    period_to_days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    assert period_to_days["30d"] == 30
    assert period_to_days.get("invalid") is None
