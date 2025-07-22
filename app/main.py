# app/main.py

from fastapi import FastAPI
from app.api import auth  # we’ll create this next
from app.db.session import engine
from app.models import user  # makes sure models are registered

app = FastAPI()

# Include routes
app.include_router(auth.router, prefix="/auth", tags=["Auth"])

@app.get("/")
def read_root():
    return {"message": "WhatsApp Clone API Running"}
