"""GlobalVest Risk Shield: deterministic PAPER-only concentration and drift checks."""

def assess_risk(decision):
    if decision.get("mode") != "PAPER" or decision.get("real_money") is not False:
        raise ValueError("Risk Shield requires PAPER mode")
    drift = decision.get("drift") or []
    if not drift:
        raise ValueError("Portfolio drift is required")
    max_drift = max(abs(float(item["drift_pct"])) for item in drift)
    max_weight = max(float(item["current_weight_pct"]) for item in drift)
    alerts = []
    if max_drift >= 5:
        alerts.append({"code": "HIGH_DRIFT", "severity": "warning", "message": "Desvio de alocacao acima de 5 pontos percentuais."})
    if max_weight > 80:
        alerts.append({"code": "CONCENTRATION", "severity": "warning", "message": "Um ativo representa mais de 80% da carteira simulada."})
    if not alerts:
        alerts.append({"code": "WITHIN_DEMO_LIMITS", "severity": "info", "message": "Nenhum limite demonstrativo de concentracao ou desvio foi excedido."})
    return {
        "engine": "GlobalVest Risk Shield",
        "version": "0.1.0",
        "mode": "PAPER",
        "real_money": False,
        "data_source": "SYNTHETIC",
        "max_drift_pp": round(max_drift, 2),
        "max_single_asset_weight_pct": round(max_weight, 2),
        "alerts": alerts,
        "execution_allowed": False,
        "limitations": "Nao mede volatilidade, liquidez, correlacao ou risco de mercado real.",
    }
