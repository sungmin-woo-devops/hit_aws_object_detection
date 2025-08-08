from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Dataset, Model, Experiment, Artifact
from schemas import DatasetCreate, Dataset, ModelCreate, Model, ExperimentCreate, Experiment, ArtifactCreate, Artifact
from uuid import UUID

router = APIRouter()

@router.post("/datasets", response_model=Dataset)
async def create_dataset(dataset: DatasetCreate, db: Session = Depends(get_db)):
    db_dataset = Dataset(**dataset.dict(exclude_unset=True))
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)
    return db_dataset

@router.post("/models", response_model=Model)
async def create_model(model: ModelCreate, db: Session = Depends(get_db)):
    db_model = Model(**model.dict(exclude_unset=True))
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model

@router.post("/experiments", response_model=Experiment)
async def create_experiment(experiment: ExperimentCreate, db: Session = Depends(get_db)):
    db_experiment = Experiment(**experiment.dict(exclude_unset=True))
    db.add(db_experiment)
    db.commit()
    db.refresh(db_experiment)
    return db_experiment

@router.post("/artifacts", response_model=Artifact)
async def create_artifact(artifact: ArtifactCreate, db: Session = Depends(get_db)):
    db_artifact = Artifact(**artifact.dict(exclude_unset=True))
    db.add(db_artifact)
    db.commit()
    db.refresh(db_artifact)
    return db_artifact