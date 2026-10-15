"""Isolated manual PAPER wallet. No broker, no real funds."""
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from app.db import engine, ManualPaperWallet, ManualPaperPosition, ManualPaperTrade

PRICES_CENTS = {"GV-WORLD": 12840, "GV-BOND": 5025, "GV-CASH": 100}

def wallet_state(account_id):
    with Session(engine) as session:
        wallet = session.get(ManualPaperWallet, account_id)
        positions = session.exec(select(ManualPaperPosition).where(ManualPaperPosition.account_id == account_id)).all()
        trades = session.exec(select(ManualPaperTrade).where(ManualPaperTrade.account_id == account_id)
                              .order_by(ManualPaperTrade.id.desc()).limit(30)).all()
        return {"cash_brl": (wallet.cash_cents if wallet else 1000000) / 100,
                "positions": [{"symbol": p.symbol, "quantity": p.quantity_micro / 1000000,
                               "market_value_brl": round(p.quantity_micro * PRICES_CENTS[p.symbol] / 100000000, 2)}
                              for p in positions if p.quantity_micro > 0],
                "trades": [{"id": t.id, "symbol": t.symbol, "side": t.side,
                            "amount_brl": t.amount_cents / 100, "quantity": t.quantity_micro / 1000000,
                            "created_at": t.created_at.isoformat()} for t in trades],
                "mode": "PAPER", "real_money": False, "broker_order_sent": False,
                "direct_execution": False}

def execute_paper(account_id, symbol, side, amount_brl):
    if symbol not in PRICES_CENTS or side not in ("BUY", "SELL"):
        raise ValueError("invalid_trade")
    cents = int((Decimal(str(amount_brl)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    if cents <= 0 or cents > 100000000:
        raise ValueError("invalid_amount")
    price = PRICES_CENTS[symbol]
    qty = int((Decimal(cents) * 1000000 / Decimal(price)).to_integral_value(rounding=ROUND_DOWN))
    if qty <= 0:
        raise ValueError("amount_too_small")
    # SQLite serializes writes; PostgreSQL row locking protects wallet updates.
    with Session(engine) as session:
        wallet = session.get(ManualPaperWallet, account_id, with_for_update=True)
        if wallet is None:
            wallet = ManualPaperWallet(account_id=account_id)
            session.add(wallet)
            session.flush()
        position = session.exec(select(ManualPaperPosition)
            .where(ManualPaperPosition.account_id == account_id)
            .where(ManualPaperPosition.symbol == symbol).with_for_update()).first()
        if position is None:
            position = ManualPaperPosition(account_id=account_id, symbol=symbol, quantity_micro=0)
            session.add(position)
            session.flush()
        if side == "BUY":
            if wallet.cash_cents < cents:
                raise ValueError("insufficient_paper_cash")
            wallet.cash_cents -= cents
            position.quantity_micro += qty
        else:
            if position.quantity_micro < qty:
                raise ValueError("insufficient_paper_position")
            position.quantity_micro -= qty
            wallet.cash_cents += cents
        trade = ManualPaperTrade(account_id=account_id, symbol=symbol, side=side,
                                 amount_cents=cents, quantity_micro=qty, price_cents=price)
        session.add(trade)
        session.commit()
        session.refresh(trade)
        return {"trade_id": trade.id, "symbol": symbol, "side": side,
                "amount_brl": cents / 100, "quantity": qty / 1000000,
                "mode": "PAPER", "real_money": False, "broker_order_sent": False,
                "direct_execution": False, "status": "PAPER_FILLED"}
