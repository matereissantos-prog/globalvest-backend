from app.ai_advisor import answer_question
from app.rebalance_engine import plan_rebalance
from app.risk_shield import assess_risk
from app.stress_lab import stress_test


def sample():
    holdings = {"GV-WORLD": 5500, "GV-BOND": 3500, "GV-CASH": 1000}
    decision = plan_rebalance(holdings, {"GV-WORLD": 55, "GV-BOND": 35, "GV-CASH": 10})
    decision["risk_profile"] = "moderate"
    return decision, assess_risk(decision), stress_test(holdings)


def test_advisor_risk():
    result = answer_question("Qual o risco?", *sample())
    assert result["topic"] == "risk"
    assert result["execution_allowed"] is False
    assert result["generative_ai_used"] is False


def test_advisor_scenario():
    result = answer_question("E se houver uma queda?", *sample())
    assert result["topic"] == "scenarios"
    assert "previsao" in result["answer"]


def test_advisor_rejects_unsafe_decision():
    decision, risk, stress = sample()
    decision["real_money"] = True
    try:
        answer_question("Qual o risco?", decision, risk, stress)
    except ValueError:
        return
    assert False, "Unsafe input accepted"


def test_advisor_rejects_empty_question():
    try:
        answer_question(" ", *sample())
    except ValueError:
        return
    assert False, "Empty question accepted"
