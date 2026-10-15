from app.stress_lab import stress_test


def test_stress_lab_equity_drop():
    result = stress_test({"GV-WORLD": 5500, "GV-BOND": 3500, "GV-CASH": 1000})
    assert result["starting_value_brl"] == 10000
    assert result["scenarios"][0]["hypothetical_value_brl"] == 8900
    assert result["scenarios"][0]["hypothetical_change_pct"] == -11
    assert result["real_money"] is False
    assert result["broker_order_sent"] is False


def test_stress_lab_combined_shock():
    result = stress_test({"GV-WORLD": 5500, "GV-BOND": 3500, "GV-CASH": 1000})
    assert result["scenarios"][2]["hypothetical_value_brl"] == 8620


def test_stress_lab_rejects_invalid_holdings():
    for holdings in ({"GV-WORLD": 100}, {"GV-WORLD": -1, "GV-BOND": 2, "GV-CASH": 3}):
        try:
            stress_test(holdings)
        except ValueError:
            continue
        assert False, "Invalid portfolio accepted"
