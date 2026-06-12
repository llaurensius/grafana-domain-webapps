from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class IncidentBase(BaseModel):
    domain_id: int
    status: str
    qualifies_as_downtime: bool
    error_type: Optional[str] = None

class IncidentCreate(IncidentBase):
    start_time: Optional[datetime] = None

class IncidentUpdate(BaseModel):
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    status: Optional[str] = None
    qualifies_as_downtime: Optional[bool] = None

class IncidentResponse(IncidentBase):
    id: int
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[int]
    domain_url: Optional[str] = None
    domain_name: Optional[str] = None
    class Config:
        from_attributes = True

from typing import List
class IncidentPaginatedResponse(BaseModel):
    total: int
    data: List[IncidentResponse]
