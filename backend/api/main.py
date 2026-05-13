"""FastAPI application entry point."""
import sys
import os

# Ensure backend/ is on the path when running from any directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.clients import router as clients_router
from api.routes.holdings import router as holdings_router
from api.routes.transactions import router as transactions_router
from api.routes.calculations import router as calculations_router
from api.routes.exports import router as exports_router
from api.db.seed_static import seed

app = FastAPI(
    title="PFIC Tool API",
    description="§1291 Excess Distribution calculator — MVP",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://pfic-tool.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clients_router)
app.include_router(holdings_router)
app.include_router(transactions_router)
app.include_router(calculations_router)
app.include_router(exports_router)


@app.on_event("startup")
def on_startup():
    """Create tables and seed static data on first run."""
    from api.deps import get_engine_once
    get_engine_once()
    seed()


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}
