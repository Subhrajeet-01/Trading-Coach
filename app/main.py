# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth.middleware import logging_middleware
from app.api import memory, session, audit, health, profile, trades

app = FastAPI(title="NevUp Trading Psychology Coach", version="1.0.0")
app.middleware("http")(logging_middleware)
app.add_middleware(CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Auth router (inline — no dependency on DB)
from fastapi import APIRouter
from pydantic import BaseModel
from app.auth.jwt_handler import issue_jwt

auth_router = APIRouter(tags=["auth"])

class LoginRequest(BaseModel):
    userId: str
    name: str | None = None

@auth_router.post("/auth/login")
async def login(body: LoginRequest):
    return {"token": issue_jwt(body.userId, body.name), "expiresIn": 86400}

app.include_router(auth_router)
app.include_router(memory.router)
app.include_router(session.router)
app.include_router(trades.router)
app.include_router(audit.router)
app.include_router(health.router)
app.include_router(profile.router)