from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas import (
    DatasetCreate, Dataset, ModelCreate, Model, 
    ExperimentCreate, Experiment, ArtifactCreate, Artifact
)
from services.data_services import (
    dataset_service, model_service, experiment_service, artifact_service
)
from core.exceptions import NotFoundError
from typing import List
from uuid import UUID

router = APIRouter()

# Dataset endpoints
@router.post("/datasets", response_model=Dataset)
async def create_dataset(dataset: DatasetCreate, db: Session = Depends(get_db)):
    return dataset_service.create(db, obj_in=dataset)

@router.get("/datasets/{dataset_id}", response_model=Dataset)
async def get_dataset(dataset_id: UUID, db: Session = Depends(get_db)):
    dataset = dataset_service.get(db, id=dataset_id)
    if not dataset:
        raise NotFoundError("Dataset", dataset_id)
    return dataset

@router.get("/datasets", response_model=List[Dataset])
async def list_datasets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return dataset_service.get_multi(db, skip=skip, limit=limit)

# Model endpoints
@router.post("/models", response_model=Model)
async def create_model(model: ModelCreate, db: Session = Depends(get_db)):
    return model_service.create(db, obj_in=model)

@router.get("/models/{model_id}", response_model=Model)
async def get_model(model_id: UUID, db: Session = Depends(get_db)):
    model = model_service.get(db, id=model_id)
    if not model:
        raise NotFoundError("Model", model_id)
    return model

@router.get("/models", response_model=List[Model])
async def list_models(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return model_service.get_multi(db, skip=skip, limit=limit)

# Experiment endpoints
@router.post("/experiments", response_model=Experiment)
async def create_experiment(experiment: ExperimentCreate, db: Session = Depends(get_db)):
    return experiment_service.create(db, obj_in=experiment)

@router.get("/experiments/{experiment_id}", response_model=Experiment)
async def get_experiment(experiment_id: UUID, db: Session = Depends(get_db)):
    experiment = experiment_service.get(db, id=experiment_id)
    if not experiment:
        raise NotFoundError("Experiment", experiment_id)
    return experiment

@router.get("/experiments", response_model=List[Experiment])
async def list_experiments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return experiment_service.get_multi(db, skip=skip, limit=limit)

# Artifact endpoints
@router.post("/artifacts", response_model=Artifact)
async def create_artifact(artifact: ArtifactCreate, db: Session = Depends(get_db)):
    return artifact_service.create(db, obj_in=artifact)

@router.get("/artifacts/{artifact_id}", response_model=Artifact)
async def get_artifact(artifact_id: UUID, db: Session = Depends(get_db)):
    artifact = artifact_service.get(db, id=artifact_id)
    if not artifact:
        raise NotFoundError("Artifact", artifact_id)
    return artifact

@router.get("/artifacts", response_model=List[Artifact])
async def list_artifacts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return artifact_service.get_multi(db, skip=skip, limit=limit)