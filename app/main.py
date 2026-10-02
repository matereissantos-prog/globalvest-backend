from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Literal

app = FastAPI(title="GlobalVest Paper Trading API", version="4.2.0")

RiskProfile = Literal["conservative", "moderate", "aggressive"]

class DemoAccountRequest(BaseModel):
    risk_profile: RiskProfile = "moderate"

class PortfolioRequest(BaseModel):
    risk_profile: RiskProfile = "moderate"
    capital_brl: float = Field(default=10000.0, gt=0, le=10000000)

POLICY = {
    "conservative": {"global_growth": 30, "defensive_fixed_income": 55, "cash_reserve": 15},
    "moderate": {"global_growth": 55, "defensive_fixed_income": 35, "cash_reserve": 10},
    "aggressive": {"global_growth": 75, "defensive_fixed_income": 15, "cash_reserve": 10},
}

# PAPER-only demo universe. These prices are deterministic simulation inputs,
# not live quotes and not investment recommendations.
ASSETS = {
    "global_growth": {
        "symbol": "GV-WORLD",
        "name": "Global Equity Basket (simulated)",
        "asset_class": "global_equity",
        "currency": "BRL",
        "price_brl": 125.00,
    },
    "defensive_fixed_income": {
        "symbol": "GV-BOND",
        "name": "Global Defensive Bond Basket (simulated)",
        "asset_class": "fixed_income",
        "currency": "BRL",
        "price_brl": 50.00,
    },
    "cash_reserve": {
        "symbol": "GV-CASH",
        "name": "Cash Reserve (simulated)",
        "asset_class": "cash",
        "currency": "BRL",
        "price_brl": 1.00,
    },
}

@app.get("/")
def root():
    return {"service":"GlobalVest","release":"4.2.0","mode":"PAPER","real_money":False}

@app.get("/health")
def health():
    return {"status":"ok","service":"globalvest-backend","release":"4.2.0","mode":"PAPER"}

@app.get("/production/readiness")
def readiness():
    return {
        "release":"4.2.0",
        "environment":"staging",
        "production_approved":False,
        "real_money_enabled":False,
        "paper_trading_enabled":True,
        "direct_execution_enabled":False,
    }

@app.get("/market/demo-assets")
def demo_assets():
    return {
        "release":"4.2.0",
        "mode":"PAPER",
        "live_market_data":False,
        "assets":[{"bucket":bucket, **data} for bucket, data in ASSETS.items()],
        "disclaimer":"Deterministic simulated prices for MVP testing only.",
    }

@app.get("/demo/journey")
def demo_journey():
    return {
        "name":"GlobalVest Paper Trading Beta",
        "starting_balance_brl":10000.0,
        "steps":["create_demo_account","complete_risk_profile","generate_portfolio","simulate_orders","view_positions_and_performance","evaluate_rebalance","collect_beta_feedback"],
        "safety":{"paper_only":True,"real_money":False,"direct_execution":False},
    }

@app.post("/demo/account")
def demo_account(payload: DemoAccountRequest):
    return {"currency":"BRL","starting_cash":10000.0,"cash":10000.0,"risk_profile":payload.risk_profile,"mode":"PAPER","real_money":False}

@app.post("/portfolio/recommendation")
def portfolio_recommendation(payload: PortfolioRequest):
    weights = POLICY[payload.risk_profile]
    allocations = {key: round(payload.capital_brl * pct / 100.0, 2) for key, pct in weights.items()}
    positions = []
    total_cost = 0.0
    for bucket, target_value in allocations.items():
        asset = ASSETS[bucket]
        qty = round(target_value / asset["price_brl"], 4)
        market_value = round(qty * asset["price_brl"], 2)
        total_cost += market_value
        positions.append({
            "bucket": bucket,
            "symbol": asset["symbol"],
            "name": asset["name"],
            "asset_class": asset["asset_class"],
            "target_weight_pct": weights[bucket],
            "simulated_price_brl": asset["price_brl"],
            "quantity": qty,
            "market_value_brl": market_value,
        })
    return {
        "engine":"GlobalVest Portfolio Engine MVP",
        "engine_version":"4.2.0",
        "mode":"PAPER",
        "real_money":False,
        "live_market_data":False,
        "risk_profile":payload.risk_profile,
        "capital_brl":round(payload.capital_brl, 2),
        "weights_pct":weights,
        "allocations_brl":allocations,
        "positions":positions,
        "total_allocated_brl":round(total_cost, 2),
        "execution":{"broker_order_sent":False,"direct_execution":False},
        "disclaimer":"Simulation only. Prices are synthetic demo inputs; no real-money order is created or transmitted.",
    }

@app.post("/portfolio/rebalance-preview")
def rebalance_preview(payload: PortfolioRequest):
    target = portfolio_recommendation(payload)
    return {
        "engine_version":"4.2.0",
        "mode":"PAPER",
        "real_money":False,
        "status":"NO_LIVE_POSITIONS",
        "action":"PREVIEW_ONLY",
        "target_positions":target["positions"],
        "orders":[],
        "broker_order_sent":False,
        "message":"Rebalance preview is enabled, but no real or broker order is generated in this MVP.",
    }
