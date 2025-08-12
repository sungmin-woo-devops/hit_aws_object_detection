from models import Dataset, Model, Experiment, Artifact
from schemas import (
    DatasetCreate, DatasetBase,
    ModelCreate, ModelBase,
    ExperimentCreate, ExperimentBase,
    ArtifactCreate, ArtifactBase
)
from .crud import CRUDService

# 각 모델에 대한 CRUD 서비스 인스턴스 생성
dataset_service = CRUDService[Dataset, DatasetCreate, DatasetBase](Dataset)
model_service = CRUDService[Model, ModelCreate, ModelBase](Model)
experiment_service = CRUDService[Experiment, ExperimentCreate, ExperimentBase](Experiment)
artifact_service = CRUDService[Artifact, ArtifactCreate, ArtifactBase](Artifact)
