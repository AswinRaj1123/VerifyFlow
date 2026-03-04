# app/main.py
from fastapi import FastAPI
from .routers import auth, sessions
from .database import engine, Base
from . import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="GTM VerifyFlow Assignment")

app.include_router(auth.router)
app.include_router(sessions.router)

@app.get("/")
def root():
    return {"message": "VerifyFlow API is running", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok"}