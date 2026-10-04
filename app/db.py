import os
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, Session, SQLModel, create_engine, select


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DemoAccount(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    device_key: str = Field(index=True, unique=True)
    risk_profile: str = Field(default="moderate", index=True)
    starting_balance_brl: float = 10000.0
    current_value_brl: float = 10000.0
    mode: str = "PAPER"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class PortfolioSnapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(index=True)
    event_type: str = Field(index=True)
    risk_profile: str
    portfolio_value_brl: float
    payload_json: str
    created_at: datetime = Field(default_factory=utc_now, index=True)


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./globalvest.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_or_create_account(device_key: str, risk_profile: str = "moderate") -> DemoAccount:
    with Session(engine) as session:
        account = session.exec(select(DemoAccount).where(DemoAccount.device_key == device_key)).first()
        if account is None:
            account = DemoAccount(device_key=device_key, risk_profile=risk_profile)
            session.add(account)
            session.commit()
            session.refresh(account)
        return account


def update_account(account_id: int, risk_profile: str, current_value_brl: float) -> DemoAccount:
    with Session(engine) as session:
        account = session.get(DemoAccount, account_id)
        if account is None:
            raise ValueError("account_not_found")
        account.risk_profile = risk_profile
        account.current_value_brl = round(current_value_brl, 2)
        account.updated_at = utc_now()
        session.add(account)
        session.commit()
        session.refresh(account)
        return account


def save_snapshot(account_id: int, event_type: str, risk_profile: str, portfolio_value_brl: float, payload_json: str) -> PortfolioSnapshot:
    with Session(engine) as session:
        snapshot = PortfolioSnapshot(
            account_id=account_id,
            event_type=event_type,
            risk_profile=risk_profile,
            portfolio_value_brl=round(portfolio_value_brl, 2),
            payload_json=payload_json,
        )
        session.add(snapshot)
        session.commit()
        session.refresh(snapshot)
        return snapshot


def list_snapshots(account_id: int, limit: int = 50):
    with Session(engine) as session:
        statement = select(PortfolioSnapshot).where(PortfolioSnapshot.account_id == account_id).order_by(PortfolioSnapshot.created_at.desc()).limit(limit)
        return list(session.exec(statement).all())
