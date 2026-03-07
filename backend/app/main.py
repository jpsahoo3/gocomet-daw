import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import rides, drivers, trips
from app.api.driver_actions import router as driver_actions_router
from app.api.payments import router as payments_router
from app.core.logging_config import setup_logging
from app.db.init_db import init_db
from app.websocket.ws import websocket_endpoint

load_dotenv()
setup_logging()


# ---------- Lifespan handler (modern FastAPI startup) ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs once on startup and shutdown.
    Replaces deprecated @app.on_event("startup").
    """
    init_db()  # create tables safely
    yield
    # (optional shutdown cleanup here)


app = FastAPI(lifespan=lifespan)


# ---------- Middleware ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Routers ----------
app.include_router(rides.router)
app.include_router(drivers.router)
app.include_router(trips.router)
app.include_router(driver_actions_router)
app.include_router(payments_router)


# ---------- WebSocket ----------
app.add_api_websocket_route("/ws", websocket_endpoint)
