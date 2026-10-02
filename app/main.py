from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Literal

app = FastAPI(title="GlobalVest Paper Trading API", version="3.4.0")

class DemoAccountRequest(BaseModel):
    risk_profile: Literal["conservative", "moderate", "aggressive"] = "moderate"

@app.get("/")
def root():
    return {"service":"GlobalVest","release":"3.4.0","mode":"PAPER","real_money":False}

@app.get("/health")
def health():
    return {"status":"ok","service":"globalvest-backend","mode":"PAPER"}

@app.get("/production/readiness")
def readiness():
    return {
        "release":"3.4.0",
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
