from decimal import Decimal, ROUND_HALF_UP

def plan_rebalance(positions, targets, threshold_pp=1.0, min_trade_brl=20.0):
    """Generate PAPER-only trade suggestions; never execute orders."""
    symbols = set(positions)
    if symbols != set(targets) or not symbols:
        raise ValueError("Assets and targets must match")
    values = {s: Decimal(str(v)) for s, v in positions.items()}
    weights = {s: Decimal(str(v)) for s, v in targets.items()}
    if any(v < 0 for v in values.values()) or any(w < 0 for w in weights.values()) or sum(weights.values()) != 100:
        raise ValueError("Invalid holdings or weights")
    total = sum(values.values())
    if total <= 0:
        raise ValueError("Empty portfolio")
    threshold = Decimal(str(threshold_pp))
    minimum = Decimal(str(min_trade_brl))
    if threshold < 0 or minimum < 0:
        raise ValueError("Invalid thresholds")
    drift, orders = [], []
    for symbol in sorted(symbols):
        current = values[symbol] / total * 100
        difference = total * weights[symbol] / 100 - values[symbol]
        drift_pp = current - weights[symbol]
        drift.append({"symbol": symbol, "target_weight_pct": float(weights[symbol]), "current_weight_pct": round(float(current), 2), "drift_pct": round(float(drift_pp), 2)})
        if abs(drift_pp) >= threshold and abs(difference) >= minimum:
            amount = abs(difference).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            orders.append({"symbol": symbol, "side": "BUY" if difference > 0 else "SELL", "notional_brl": float(amount), "paper_only": True})
    return {"mode": "PAPER", "real_money": False, "live_market_data": False, "status": "REBALANCE_PROPOSED" if orders else "NO_ACTION", "action": "DECISION_ONLY", "portfolio_value_brl": float(total), "drift_threshold_pp": float(threshold), "min_trade_brl": float(minimum), "drift": drift, "orders": orders, "broker_order_sent": False, "direct_execution": False, "persisted": False}
