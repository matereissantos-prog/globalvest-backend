"""Deterministic hypothetical stress scenarios; never a market forecast."""
from decimal import Decimal, ROUND_HALF_UP

SCENARIOS = (
    ("GLOBAL_EQUITY_DROP_20", "Bolsa global -20%", {"GV-WORLD": "-0.20", "GV-BOND": "0", "GV-CASH": "0"}),
    ("GLOBAL_EQUITY_DROP_35", "Bolsa global -35%", {"GV-WORLD": "-0.35", "GV-BOND": "0", "GV-CASH": "0"}),
    ("EQUITY_AND_BONDS_DROP", "Bolsa -20% e renda fixa -8%", {"GV-WORLD": "-0.20", "GV-BOND": "-0.08", "GV-CASH": "0"}),
)

def stress_test(holdings):
    if not holdings or set(holdings) != {"GV-WORLD", "GV-BOND", "GV-CASH"}:
        raise ValueError("Invalid simulated holdings")
    values = {key: Decimal(str(value)) for key, value in holdings.items()}
    if any(not v.is_finite() or v < 0 for v in values.values()):
        raise ValueError("Invalid values")
    total = sum(values.values())
    if total <= 0:
        raise ValueError("Empty portfolio")
    def money(value):
        return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    scenarios = []
    for code, label, shocks in SCENARIOS:
        stressed = sum(values[symbol] * (1 + Decimal(shocks[symbol])) for symbol in values)
        delta = stressed - total
        scenarios.append({
            "code": code, "label": label, "hypothetical_value_brl": money(stressed),
            "hypothetical_change_brl": money(delta),
            "hypothetical_change_pct": round(float(delta / total * 100), 2),
            "shocks_pct": {symbol: float(Decimal(shock) * 100) for symbol, shock in shocks.items()},
        })
    return {
        "mode": "PAPER", "real_money": False, "live_market_data": False,
        "engine": "GlobalVest Stress Lab", "version": "0.1.0",
        "starting_value_brl": money(total), "scenarios": scenarios,
        "broker_order_sent": False, "direct_execution": False,
        "disclaimer": "Cenarios hipoteticos com ativos e precos sinteticos. Nao sao previsoes, VaR ou estimativas de probabilidade.",
    }
