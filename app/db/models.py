from sqlalchemy import String, Boolean, DateTime, Float, Integer, Column, UniqueConstraint
from datetime import datetime
from .base import Base

class Ticker(Base):
    __tablename__ = "tickers"
    id = Column(Integer, primary_key=True)
    symbol = Column(String(12), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class Price(Base):
    __tablename__ = "prices"
    id = Column(Integer, primary_key=True)
    symbol = Column(String(12), nullable=False, index=True)
    ts = Column(DateTime, nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("symbol", "ts", name="uq_symbol_ts"),)
