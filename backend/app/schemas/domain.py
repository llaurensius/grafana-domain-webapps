from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DomainBase(BaseModel):
    url: str
    name: str
    is_active: bool = True

class DomainCreate(DomainBase):
    pass

class DomainUpdate(BaseModel):
    url: Optional[str] = None
    name: Optional[str] = None
    is_active: Optional[bool] = None

class DomainResponse(DomainBase):
    id: int
    created_at: datetime
    status: Optional[str] = "UNKNOWN"
    ssl_info: Optional[str] = None
    error_info: Optional[str] = None

    class Config:
        from_attributes = True

class BulkDeleteRequest(BaseModel):
    ids: list[int]
