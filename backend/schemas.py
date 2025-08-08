from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

# 1. UserBase, UserCreate, User: 재사용성과 책임 분리
# 공통 필드를 정의하는 기본 클래스 
class UserBase(BaseModel):
    # 여러 모델에서 중복 정의를 피하기 위해 필드를 한 곳에 모아놓음
    email: str
    api_token: Optional[str] = None
    role: str = "user"

# 사용자 생성 (for Request)
class UserCreate(UserBase):
    # 역할: 사용자 생성 시 클라이언트가 제공해야 하는 데이터를 정의
    # 추가적인 필드를 포함 X, 왜 따로 정의?
    # 클라이언트가 보내는 입력 스키마 정의하여, 요청 데이터 검증 시 사용
    # 만약 User 클래스 직접 사용 시, id나 created_at 실수로 포함될 수 있음
    # 또한 다른 엔드포인트(예: 사용자 업데이트)에서도 재사용될 수 있음
    pass

# 사용자 조회 (for Response)
class User(UserBase):
    # 역할: 데이터베이스에서 조회된 사용자 데이터를 표현하는 응답 스키마
    # API 응답으로 클라이언트에게 반환되는 데이터는 보통 입력 데이터보다 더 많은 정보를 포함
    # (예: 데이터베이스에서 생성된 고유 ID나 타임스탬프)
    id: UUID
    created_at: datetime
    updated_at: datetime

    # Pydantic 모델의 메타데이터나 동작 방식을 정의
    # Pydantic이 ORM(Object-Relational Mapping) 객체(예: SQLAlchemy 모델)와 호환되도록 설정
    class Config:
        # Pydantix이 ORM 객체의 속성을 자동으로 읽어 Pydantic 모델로 변환
        # 데이터베이스에서 조회한 ORM 객체를 Pydantic 모델로 변환하여 JSON으로 반환
        orm_mode = True 


class DatasetBase(BaseModel):
    name: str
    description: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class DatasetCreate(DatasetBase):
    pass

class Dataset(DatasetBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ModelBase(BaseModel):
    name: str
    version: str
    framework: str
    format: str
    file_size: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    dataset_id: Optional[UUID] = None
    created_by: Optional[UUID] = None

class ModelCreate(ModelBase):
    pass

class Model(ModelBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ExperimentBase(BaseModel):
    model_id: UUID
    name: str
    framework: str
    hyperparameters: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created_by: Optional[UUID] = None

class ExperimentCreate(ExperimentBase):
    pass

class Experiment(ExperimentBase):
    id: UUID
    created_at: datetime

    class Config:
        orm_mode = True

class ArtifactBase(BaseModel):
    run_id: str
    artifact_type: str
    description: Optional[str] = None
    file_name: str
    file_type: str

class ArtifactCreate(ArtifactBase):
    pass

class Artifact(ArtifactBase):
    id: UUID
    created_at: datetime

    class Config:
        orm_mode = True

