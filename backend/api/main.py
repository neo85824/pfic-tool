"""FastAPI application entry point."""
import sys
import os
from contextlib import asynccontextmanager

# Ensure backend/ is on the path when running from any directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.auth import router as auth_router
from api.routes.clients import router as clients_router
from api.routes.holdings import router as holdings_router
from api.routes.transactions import router as transactions_router
from api.routes.calculations import router as calculations_router
from api.routes.exports import router as exports_router
from api.db.seed_static import seed

_DEFAULT_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://pfic-tool.vercel.app",
]
_extra = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
ALLOWED_ORIGINS = _DEFAULT_ORIGINS + _extra


@asynccontextmanager
async def lifespan(app: FastAPI):
    from api.deps import get_engine_once
    get_engine_once()
    seed()
    yield


app = FastAPI(
    title="PFIC Tool API",
    description="§1291 Excess Distribution calculator — MVP",
    version=os.getenv("APP_VERSION", "0.1.0"),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(clients_router)
app.include_router(holdings_router)
app.include_router(transactions_router)
app.include_router(calculations_router)
app.include_router(exports_router)


@app.get("/health")
def health():
    return {"status": "ok", "version": os.getenv("APP_VERSION", "0.1.0")}
