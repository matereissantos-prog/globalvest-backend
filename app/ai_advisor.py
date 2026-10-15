"""Read-only, rule-based investment assistant for synthetic PAPER portfolios.

No generative model, external feeds, trading actions, or personal advice.
"""
import unicodedata
import re

TOPICS = ("overview", "risk", "rebalance", "scenarios", "limitations")

def _normalize(value):
    return "".join(c for c in unicodedata.normalize("NFKD", value.lower()) if not unicodedata.combining(c))

def answer_question(question, decision, risk, stress):
    if not isinstance(question, str) or not question.strip() or len(question) > 500:
        raise ValueError("Question must contain 1-500 characters")
    if decision.get("mode") != "PAPER" or decision.get("real_money") is not False:
        raise ValueError("Unsafe decision")
    if risk.get("mode") != "PAPER" or stress.get("mode") != "PAPER":
        raise ValueError("Unsafe data source")
    q = _normalize(question)
    if any(word in q for word in ("cenario", "queda", "crise", "perder", "simulacao", "cair", "cai", "despenc", "bolsa")):
        topic = "scenarios"
        percentage = re.search(r"(?<!\\d)(\\d{1,3})\\s*%", q)
        selected = None
        if percentage:
            shock = -int(percentage.group(1))
            for scenario in stress["scenarios"]:
                if scenario["shocks_pct"].get("GV-WORLD") == shock and scenario["shocks_pct"].get("GV-BOND") == 0:
                    selected = scenario
                    break
        if selected is None and percentage:
            answer = ("Nao ha um cenario cadastrado para a queda solicitada. "
                      "Consulte o simulador para ver os cenarios disponiveis; nao vou inventar um calculo.")
        else:
            selected = selected or min(stress["scenarios"], key=lambda item: item["hypothetical_change_pct"])
            answer = ("No cenario hipotetico %s, a carteira de R$ %.2f passaria a R$ %.2f "
                      "(variacao de %.2f%%, ou R$ %.2f). Isso nao e previsao nem perda maxima." %
                      (selected["label"], stress["starting_value_brl"],
                       selected["hypothetical_value_brl"], selected["hypothetical_change_pct"],
                       selected["hypothetical_change_brl"]))
    elif any(word in q for word in ("rebalance", "comprar", "vender", "ajust", "decisao")):
        topic = "rebalance"
        action = "manter a carteira" if decision["status"] == "NO_ACTION" else "propor ajustes apenas simulados"
        answer = ("A regra atual indica %s. Limite de desvio: %.2f ponto(s) percentual(is); "
                  "nenhuma ordem sera enviada." % (action, decision["drift_threshold_pp"]))
    elif any(word in q for word in ("risco", "concentr", "desvio", "protec")):
        topic = "risk"
        answer = ("Maior concentracao simulada: %.2f%%; maior desvio: %.2f p.p. "
                  "O Risk Shield verifica apenas concentracao e desvio, nao risco total de mercado." %
                  (risk["max_single_asset_weight_pct"], risk["max_drift_pp"]))
    elif any(word in q for word in ("real", "ia", "dados", "limite", "funciona")):
        topic = "limitations"
        answer = ("Esta versao usa regras verificaveis e dados sinteticos, nao IA generativa ou cotacoes reais. "
                  "Nao executa operacoes, nao oferece recomendacao personalizada e nao garante retorno.")
    else:
        topic = "overview"
        answer = ("A carteira demonstrativa vale R$ %.2f e segue o perfil %s. "
                  "Posso explicar riscos, rebalanceamento e cenarios simulados." %
                  (decision["portfolio_value_brl"], decision["risk_profile"]))
    return {
        "assistant": "GlobalVest AI Advisor Preview",
        "assistant_version": "rules-0.2.0",
        "mode": "PAPER", "real_money": False, "generative_ai_used": False,
        "topic": topic, "answer": answer,
        "source": "synthetic_portfolio_rules",
        "execution_allowed": False, "broker_order_sent": False,
        "disclaimer": "Educacao e demonstracao; nao e aconselhamento financeiro individual.",
    }
