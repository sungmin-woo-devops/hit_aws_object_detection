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
from database import supabase
from utils.supabase import get_supabase_client
from utils.mongodb import get_mongo_collection
from routes.artifacts import router as artifacts_router

app = FastAPI()

# CRUD for Users
@app.port("/users", response_model=User)
async def create_user(user: UserCreate):
    try:
        response = supabase.table("users").insert(user.dict(exclude_unset=True)).execute()
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users", response_model=List[User]):
async def list_users():
    response = supabase.table("users").select("*").execute()
    return response.data

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: UUID):
    response = supabase.table("users").select("*").eq("id", str(user_id)).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="User not found")
    return response.data[0]

@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: UUID, user: UserCreate):
    response = supabase.table("users").update(user.dict(exclude_unset=True)).eq("id", str(user_id)).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="User not found")
    return response.data[0]

@app.delete("/users/{user_id}")
async def delete_user(user_id: UUID):
    response = supabase.table("users").delete().eq("id", str(user_id)).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted"}

# CRUD for Datasets
@app.post("/datasets", response_model=Dataset)
async def create_dataset(dataset: DatasetCreate):
    try:
        response = supabase.table("datasets").insert(dataset.dict(exclude_unset=True)).execute()
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/datasets", response_model=List[Dataset])
async def list_datasets():
    response = supabase.table("datasets").select("*").execute()
    return response.data

# CRUD for Models
@app.post("/models", response_model=Model)
async def create_model(model: ModelCreate):
    try:
        response = supabase.table("models").insert(model.dict(exclude_unset=True)).execute()
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/models", response_model=List[Model])
async def list_models():
    response = supabase.table("models").select("*").execute()
    return response.data

# CRUD for Experiments
@app.post("/experiments", response_model=Experiment)
async def create_experiment(experiment: ExperimentCreate):
    try:
        response = supabase.table("experiments").insert(experiment.dict(exclude_unset=True)).execute()
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/experiments", response_model=List[Experiment])
async def list_experiments():
    response = supabase.table("experiments").select("*").execute()
    return response.data

# Seed Dummy Data
@app.post("/seed-data")
async def seed_data():
    try:
        # Insert users
        users = generate_dummy_users(3)
        user_response = supabase.table("users").insert(users).execute()
        user_ids = [user["id"] for user in user_response.data]

        # Insert datasets
        datasets = generate_dummy_datasets(3)
        dataset_response = supabase.table("datasets").insert(datasets).execute()
        dataset_ids = [dataset["id"] for dataset in dataset_response.data]

        # Insert models
        models = generate_dummy_models(3, dataset_ids, user_ids)
        model_response = supabase.table("models").insert(models).execute()
        model_ids = [model["id"] for model in model_response.data]

        # Insert experiments
        experiments = generate_dummy_experiments(3, model_ids, user_ids)
        supabase.table("experiments").insert(experiments).execute()

        return {"message": "Dummy data inserted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
