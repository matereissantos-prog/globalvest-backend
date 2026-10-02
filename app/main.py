from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Literal

app = FastAPI(title="GlobalVest Paper Trading API", version="4.1.0")

RiskProfile = Literal["conservative", "moderate", "aggressive"]

class DemoAccountRequest(BaseModel):
    risk_profile: RiskProfile = "moderate"

class PortfolioRequest(BaseModel):
    risk_profile: RiskProfile = "moderate"
    capital_brl: float = Field(default=10000.0, gt=0, le=10000000)

# Policy portfolios for the MVP. The allocation is calculated server-side so
# the Android client no longer needs to own the portfolio rules.
POLICY = {
    "conservative": {"global_growth": 30, "defensive_fixed_income": 55, "cash_reserve": 15},
    "moderate": {"global_growth": 55, "defensive_fixed_income": 35, "cash_reserve": 10},
    "aggressive": {"global_growth": 75, "defensive_fixed_income": 15, "cash_reserve": 10},
}

@app.get("/")
def root():
    return {"service":"GlobalVest","release":"4.1.0","mode":"PAPER","real_money":False}

@app.get("/health")
def health():
    return {"status":"ok","service":"globalvest-backend","release":"4.1.0","mode":"PAPER"}

@app.get("/production/readiness")
def readiness():
    return {
        "release":"4.1.0",
        "environment":"staging",
        "production_approved":False,
        "real_money_enabled":False,
        "paper_trading_enabled":True,
        "direct_execution_enabled":False
    }

@app.get("/demo/journey")
def demo_journey():
    return {
        "name":"GlobalVest Paper Trading Beta",
        "starting_balance_brl":10000.0,
        "steps":["create_demo_account","complete_risk_profile","generate_portfolio","simulate_orders","view_positions_and_performance","evaluate_rebalance","collect_beta_feedback"],
        "safety":{"paper_only":True,"real_money":False,"direct_execution":False}
    }

@app.post("/demo/account")
def demo_account(payload: DemoAccountRequest):
    return {"currency":"BRL","starting_cash":10000.0,"cash":10000.0,"risk_profile":payload.risk_profile,"mode":"PAPER","real_money":False}

@app.post("/portfolio/recommendation")
def portfolio_recommendation(payload: PortfolioRequest):
    weights = POLICY[payload.risk_profile]
    allocations = {
        key: round(payload.capital_brl * pct / 100.0, 2)
        for key, pct in weights.items()
    }
    return {
        "engine":"GlobalVest Portfolio Engine MVP",
        "engine_version":"4.1.0",
        "mode":"PAPER",
        "real_money":False,
        "risk_profile":payload.risk_profile,
        "capital_brl":round(payload.capital_brl, 2),
        "weights_pct":weights,
        "allocations_brl":allocations,
        "total_allocated_brl":round(sum(allocations.values()), 2),
        "execution":{"broker_order_sent":False,"direct_execution":False},
        "disclaimer":"Demonstration portfolio only. No real-money order is created or transmitted."
    }
