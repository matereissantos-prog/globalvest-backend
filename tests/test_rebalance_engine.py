from app.rebalance_engine import plan_rebalance

def test_no_action_with_small_drift():
    result = plan_rebalance({"GV-WORLD": 5657.1, "GV-BOND": 3510, "GV-CASH": 1000}, {"GV-WORLD": 55, "GV-BOND": 35, "GV-CASH": 10})
    assert result["status"] == "NO_ACTION"
    assert result["orders"] == []
    assert result["broker_order_sent"] is False
    assert result["direct_execution"] is False

def test_proposes_paper_orders_only():
    result = plan_rebalance({"GV-WORLD": 7000, "GV-BOND": 2000, "GV-CASH": 1000}, {"GV-WORLD": 55, "GV-BOND": 35, "GV-CASH": 10})
    assert result["status"] == "REBALANCE_PROPOSED"
    assert any(o["side"] == "SELL" for o in result["orders"])
    assert any(o["side"] == "BUY" for o in result["orders"])
    assert all(o["paper_only"] for o in result["orders"])
    assert result["real_money"] is False

def test_invalid_weights():
    try:
        plan_rebalance({"A": 100}, {"A": 80})
    except ValueError:
        return
    assert False, "Expected ValueError"
