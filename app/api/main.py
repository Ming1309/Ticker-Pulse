from fastapi import FastAPI
from app.db.base import engine
from app.db.models import Base

app = FastAPI(title="TickerPulse")

@app.get("/health")
def health():
    return {"status": "ok"}
