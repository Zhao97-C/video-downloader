from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import download, auth, payment, ai, config
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="SaveAny API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(config.router, prefix="/api/config")
app.include_router(download.router, prefix="/api")
app.include_router(auth.router, prefix="/api/auth")
app.include_router(payment.router, prefix="/api/payment")
app.include_router(ai.router, prefix="/api/ai")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
