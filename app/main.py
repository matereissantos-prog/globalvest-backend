import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Literal

from app.rebalance_engine import plan_rebalance
from app.db import create_db_and_tables, get_or_create_account, list_snapshots, save_snapshot, update_account

app = FastAPI(title="GlobalVest Paper Trading API", version="4.4.0")

RiskProfile = Literal["conservative", "moderate", "aggressive"]

class DemoAccountRequest(BaseModel):
    risk_profile: RiskProfile = "moderate"
    device_key: str = Field(default="globalvest-demo", min_length=3, max_length=100)

class PortfolioRequest(BaseModel):
    risk_profile: RiskProfile = "moderate"
    capital_brl: float = Field(default=10000.0, gt=0, le=10000000)

POLICY = {
    "conservative": {"global_growth": 30, "defensive_fixed_income": 55, "cash_reserve": 15},
    "moderate": {"global_growth": 55, "defensive_fixed_income": 35, "cash_reserve": 10},
    "aggressive": {"global_growth": 75, "defensive_fixed_income": 15, "cash_reserve": 10},
}

ASSETS = {
    "global_growth": {"symbol":"GV-WORLD","name":"Global Equity Basket (simulated)","asset_class":"global_equity","currency":"BRL","price_brl":125.00},
    "defensive_fixed_income": {"symbol":"GV-BOND","name":"Global Defensive Bond Basket (simulated)","asset_class":"fixed_income","currency":"BRL","price_brl":50.00},
    "cash_reserve": {"symbol":"GV-CASH","name":"Cash Reserve (simulated)","asset_class":"cash","currency":"BRL","price_brl":1.00},
}

DEMO_PRICE_PATH = {
    "GV-WORLD": [125.00, 126.25, 124.80, 127.10, 128.40],
    "GV-BOND": [50.00, 50.10, 50.05, 50.20, 50.25],
    "GV-CASH": [1.00, 1.00, 1.00, 1.00, 1.00],
}

@app.on_event("startup")
def startup():
    create_db_and_tables()

@app.get("/")
def root():
    return {"service":"GlobalVest","release":"4.4.0","mode":"PAPER","real_money":False,"persistence":True}

@app.get("/health")
def health():
    return {"status":"ok","service":"globalvest-backend","release":"4.4.0","mode":"PAPER"}

@app.get("/production/readiness")
def readiness():
    return {"release":"4.4.0","environment":"staging","production_approved":False,"real_money_enabled":False,"paper_trading_enabled":True,"direct_execution_enabled":False,"persistent_accounts_enabled":True}

@app.get("/market/demo-assets")
def demo_assets():
    return {"release":"4.4.0","mode":"PAPER","live_market_data":False,"assets":[{"bucket":bucket, **data} for bucket, data in ASSETS.items()],"disclaimer":"Deterministic simulated prices for MVP testing only."}

@app.get("/demo/journey")
def demo_journey():
    return {"name":"GlobalVest Paper Trading Beta","starting_balance_brl":10000.0,"steps":["create_demo_account","complete_risk_profile","generate_portfolio","simulate_orders","view_positions_and_performance","evaluate_rebalance","collect_beta_feedback"],"safety":{"paper_only":True,"real_money":False,"direct_execution":False}}

@app.post("/demo/account")
def demo_account(payload: DemoAccountRequest):
    account = get_or_create_account(payload.device_key, payload.risk_profile)
    if account.risk_profile != payload.risk_profile:
        account = update_account(account.id, payload.risk_profile, account.current_value_brl)
    return {"account_id":account.id,"device_key":account.device_key,"currency":"BRL","starting_cash":account.starting_balance_brl,"current_value_brl":account.current_value_brl,"risk_profile":account.risk_profile,"mode":"PAPER","real_money":False,"persistent":True}

@app.get("/demo/account/{device_key}")
def read_demo_account(device_key: str):
    account = get_or_create_account(device_key)
    return {"account_id":account.id,"device_key":account.device_key,"starting_balance_brl":account.starting_balance_brl,"current_value_brl":account.current_value_brl,"risk_profile":account.risk_profile,"mode":account.mode,"persistent":True}

@app.get("/demo/account/{device_key}/snapshots")
def account_snapshots(device_key: str, limit: int = 20):
    account = get_or_create_account(device_key)
    rows = list_snapshots(account.id, min(max(limit, 1), 100))
    return {"account_id":account.id,"device_key":account.device_key,"count":len(rows),"snapshots":[{"id":r.id,"event_type":r.event_type,"risk_profile":r.risk_profile,"portfolio_value_brl":r.portfolio_value_brl,"created_at":r.created_at,"payload":json.loads(r.payload_json)} for r in rows]}

def build_positions(payload: PortfolioRequest, price_index: int = 0):
    weights = POLICY[payload.risk_profile]
    allocations = {key: round(payload.capital_brl * pct / 100.0, 2) for key, pct in weights.items()}
    positions = []
    total = 0.0
    for bucket, target_value in allocations.items():
        asset = ASSETS[bucket]
        symbol = asset["symbol"]
        initial_price = DEMO_PRICE_PATH[symbol][0]
        current_price = DEMO_PRICE_PATH[symbol][price_index]
        qty = round(target_value / initial_price, 4)
        market_value = round(qty * current_price, 2)
        total += market_value
        positions.append({"bucket":bucket,"symbol":symbol,"name":asset["name"],"asset_class":asset["asset_class"],"target_weight_pct":weights[bucket],"simulated_price_brl":current_price,"quantity":qty,"market_value_brl":market_value})
    return weights, allocations, positions, round(total, 2)

@app.post("/portfolio/recommendation")
def portfolio_recommendation(payload: PortfolioRequest):
    weights, allocations, positions, total = build_positions(payload, 0)
    return {"engine":"GlobalVest Portfolio Engine MVP","engine_version":"4.4.0","mode":"PAPER","real_money":False,"live_market_data":False,"risk_profile":payload.risk_profile,"capital_brl":round(payload.capital_brl,2),"weights_pct":weights,"allocations_brl":allocations,"positions":positions,"total_allocated_brl":total,"execution":{"broker_order_sent":False,"direct_execution":False},"disclaimer":"Simulation only. Prices are synthetic demo inputs; no real-money order is created or transmitted."}

@app.post("/portfolio/history")
def portfolio_history(payload: PortfolioRequest):
    points=[]
    labels=["D0","D1","D2","D3","D4"]
    for idx,label in enumerate(labels):
        _,_,positions,total=build_positions(payload, idx)
        points.append({"period":label,"portfolio_value_brl":total,"positions":positions})
    start=points[0]["portfolio_value_brl"]
    end=points[-1]["portfolio_value_brl"]
    return {"engine_version":"4.4.0","mode":"PAPER","real_money":False,"live_market_data":False,"risk_profile":payload.risk_profile,"starting_value_brl":start,"current_value_brl":end,"return_pct":round((end/start-1)*100,2),"history":points,"disclaimer":"Synthetic performance history for demonstration only."}

@app.post("/portfolio/rebalance-preview")
def rebalance_preview(payload: PortfolioRequest):
    target_weights = POLICY[payload.risk_profile]
    _,_,positions,current_total = build_positions(payload, 4)
    orders=[]
    drift=[]
    for p in positions:
        current_weight = round((p["market_value_brl"] / current_total) * 100, 2) if current_total else 0.0
        target_weight = target_weights[p["bucket"]]
        drift_pct = round(current_weight - target_weight, 2)
        target_value = round(current_total * target_weight / 100.0, 2)
        delta_value = round(target_value - p["market_value_brl"], 2)
        drift.append({"symbol":p["symbol"],"target_weight_pct":target_weight,"current_weight_pct":current_weight,"drift_pct":drift_pct})
        if abs(drift_pct) >= 0.50 and abs(delta_value) >= 1.0:
            orders.append({"symbol":p["symbol"],"side":"BUY" if delta_value > 0 else "SELL","notional_brl":round(abs(delta_value),2),"paper_only":True})
    return {"engine_version":"4.4.0","mode":"PAPER","real_money":False,"live_market_data":False,"status":"PREVIEW_READY","action":"PREVIEW_ONLY","portfolio_value_brl":current_total,"drift":drift,"orders":orders,"broker_order_sent":False,"direct_execution":False,"message":"Rebalance preview only. No broker or real-money order is generated."}

@app.post("/demo/account/{device_key}/snapshot")
def create_account_snapshot(device_key: str, payload: PortfolioRequest):
    account = get_or_create_account(device_key, payload.risk_profile)
    _,_,positions,total = build_positions(payload, 4)
    body = {"positions":positions,"source":"synthetic_demo_path","paper_only":True}
    account = update_account(account.id, payload.risk_profile, total)
    snapshot = save_snapshot(account.id, "portfolio_mark", payload.risk_profile, total, json.dumps(body))
    return {"status":"SAVED","snapshot_id":snapshot.id,"account_id":account.id,"device_key":device_key,"current_value_brl":account.current_value_brl,"risk_profile":account.risk_profile,"mode":"PAPER","real_money":False}


@app.post("/portfolio/rebalance-decision")
def rebalance_decision(payload: PortfolioRequest):
    """PAPER-only decision; no order is submitted or persisted."""
    _, _, positions, _ = build_positions(payload, 4)
    holdings = {p["symbol"]: p["market_value_brl"] for p in positions}
    targets = {ASSETS[bucket]["symbol"]: weight for bucket, weight in POLICY[payload.risk_profile].items()}
    result = plan_rebalance(holdings, targets, threshold_pp=1.0, min_trade_brl=20.0)
    return {"engine_version": "5.0.0", "risk_profile": payload.risk_profile, **result}
