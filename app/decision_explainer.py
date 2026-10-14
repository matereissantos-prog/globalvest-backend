"""Deterministic, auditable explanations for PAPER decisions.

This module is not a generative AI model and makes no return forecasts.
"""

def explain_rebalance(decision):
    if decision.get("mode") != "PAPER" or decision.get("real_money") is not False:
        raise ValueError("Unsafe decision")
    drift = decision["drift"]
    largest = max(drift, key=lambda item: abs(item["drift_pct"]))
    threshold = decision["drift_threshold_pp"]
    if decision["status"] == "NO_ACTION":
        summary = "Manter a carteira simulada: os desvios nao exigem ajustes pela politica atual."
        reason = "Maior desvio observado: %.2f p.p. em %s; limite: %.2f p.p." % (abs(largest["drift_pct"]), largest["symbol"], threshold)
    else:
        summary = "A politica sugere ajustes simulados para aproximar os pesos dos alvos."
        reason = "Maior desvio observado: %.2f p.p. em %s; limite: %.2f p.p." % (abs(largest["drift_pct"]), largest["symbol"], threshold)
    return {
        "explanation_version": "rules-1.0",
        "explanation_type": "DETERMINISTIC_RULES",
        "generative_ai_used": False,
        "summary": summary,
        "reason": reason,
        "risk_notes": [
            "Precos e ativos sao sinteticos; esta analise nao usa cotacoes reais.",
            "Rebalanceamento nao elimina perdas nem garante retorno.",
            "Perfil de risco e pesos-alvo sao parametros de demonstracao.",
        ],
        "human_readable": True,
        "execution_allowed": False,
    }
