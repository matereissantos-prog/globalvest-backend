from app.rebalance_engine import plan_rebalance
from app.decision_explainer import explain_rebalance


def test_explanation_no_action():
    decision = plan_rebalance({"GV-WORLD": 5657.1, "GV-BOND": 3510, "GV-CASH": 1000}, {"GV-WORLD": 55, "GV-BOND": 35, "GV-CASH": 10})
    result = explain_rebalance(decision)
    assert decision["status"] == "NO_ACTION"
    assert result["generative_ai_used"] is False
    assert result["execution_allowed"] is False
    assert "GV-WORLD" in result["reason"]


def test_explanation_rebalance_proposed():
    decision = plan_rebalance({"GV-WORLD": 7000, "GV-BOND": 2000, "GV-CASH": 1000}, {"GV-WORLD": 55, "GV-BOND": 35, "GV-CASH": 10})
    result = explain_rebalance(decision)
    assert decision["status"] == "REBALANCE_PROPOSED"
    assert result["explanation_type"] == "DETERMINISTIC_RULES"


def test_reject_unsafe_decision():
    decision = plan_rebalance({"A": 100}, {"A": 100})
    decision["real_money"] = True
    try:
        explain_rebalance(decision)
    except ValueError:
        return
    assert False, "Unsafe decision was accepted"
