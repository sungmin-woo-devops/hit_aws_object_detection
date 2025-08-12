from pydantic import BaseModel, Field
from typing import List, Optional

class Service(BaseModel):
    name: str
    count: Optional[int] = 1
    labels: List[str] = []

class Connection(BaseModel):
    from_: str = Field(alias="from")
    to: str
    protocol: Optional[str] = ""
    notes: Optional[str] = ""

class Networking(BaseModel):
    vpcs: List[str] = []
    subnets: List[str] = []
    security_groups: List[str] = []

class DataStore(BaseModel):
    name: str
    notes: Optional[str] = ""

class DiagramExtract(BaseModel):
    services: List[Service] = []
    connections: List[Connection] = []
    networking: Networking = Networking()
    data_stores: List[DataStore] = []
