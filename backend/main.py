import re
from fastapi import FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated, List, Dict, Optional
from uuid import UUID
from models import (
    User, UserCreate, 
    Dataset, DatasetCreate, 
    Model, ModelCreate, 
    Experiment, ExperimentCreate,
    Artifact
)
from database import get_db
from utils import get_supabase_client, get_mongo_collection
from routes.artifacts import router as artifacts_router
from routes.auth import router as auth_router
from routes.data import router as data_router

app = FastAPI()

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(data_router, prefix="/data", tags=["data"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
