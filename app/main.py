import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.upload import router as upload_router
from app.routes.missions import router as missions_router
from app.services.db import get_supabase

APP_NAME = os.getenv("APP_NAME", "OryzAID Cloud API")
ENV = os.getenv("ENVIRONMENT", "development")

app = FastAPI(title=APP_NAME)

app.include_router(upload_router)
app.include_router(missions_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "running", "app": APP_NAME, "environment": ENV}

@app.get("/health")
def health_check():
    return {"status": "ok", "app": APP_NAME, "environment": ENV}

@app.get("/test-db")
def test_db():
    try:
        sb = get_supabase()
        res = sb.table("missions").select("*").limit(1).execute()
        return {"ok": True, "data": res.data}
    except Exception as e:
        return {"ok": False, "error": str(e)}

