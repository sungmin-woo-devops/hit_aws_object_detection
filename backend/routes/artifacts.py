from fastapi import APIRouter
from models.artifact import Artifact
from database import artifacts

router = APIRouter()

@router.post("/artifacts/")
def create_artifact(artifact: Artifact):
    artifacts.append(artifact)
    return {"message": "Artifact saved", "artifact": artifact}

@router.get("/artifacts/")
def list_artifacts():
    return artifacts