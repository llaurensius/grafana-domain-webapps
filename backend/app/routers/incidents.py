from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.incident import IncidentResponse
from app.repositories.incident_repo import IncidentRepository

router = APIRouter()

from app.schemas.incident import IncidentPaginatedResponse

@router.get("/", response_model=IncidentPaginatedResponse)
def get_all_incidents(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    skip = max(0, skip)
    limit = max(1, min(100, limit))
    repo = IncidentRepository(db)
    return repo.get_all(skip=skip, limit=limit)
