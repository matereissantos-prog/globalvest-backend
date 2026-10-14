from app.rebalance_engine import plan_rebalance
from app.risk_shield import assess_risk


def test_risk_shield_normal():
    d = plan_rebalance({"A": 55, "B": 35, "C": 10}, {"A": 55, "B": 35, "C": 10})
    result = assess_risk(d)
    assert result["alerts"][0]["code"] == "WITHIN_DEMO_LIMITS"
    assert result["execution_allowed"] is False


def test_risk_shield_alerts():
    d = plan_rebalance({"A": 90, "B": 5, "C": 5}, {"A": 55, "B": 35, "C": 10})
    codes = {alert["code"] for alert in assess_risk(d)["alerts"]}
    assert "HIGH_DRIFT" in codes
    assert "CONCENTRATION" in codes


def test_risk_shield_rejects_live():
    d = plan_rebalance({"A": 100}, {"A": 100})
    d["real_money"] = True
    try:
        assess_risk(d)
    except ValueError:
        return
    assert False, "Live decision was accepted"
