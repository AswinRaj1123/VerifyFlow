from fastapi import FastAPI
from .database import Base, engine

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Backend running"}