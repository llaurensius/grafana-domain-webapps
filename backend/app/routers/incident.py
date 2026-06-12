from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.incident import IncidentResponse
from app.repositories.incident import IncidentRepository
from app.services.auth import AuthService
from app.models.user import User
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])

@router.get("/", response_model=List[IncidentResponse])
def get_incidents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    domain_id: Optional[int] = Query(None),
    qualifies_only: Optional[bool] = Query(None),
    status: Optional[str] = Query(None),
    error_category: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None, description="Format ISO: YYYY-MM-DDTHH:MM:SS"),
    end_date: Optional[str] = Query(None, description="Format ISO: YYYY-MM-DDTHH:MM:SS"),
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    repo = IncidentRepository(db)
    
    start_dt = None
    end_dt = None
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            pass
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            pass

    incidents = repo.get_all(
        skip=skip,
        limit=limit,
        domain_id=domain_id,
        qualifies_only=qualifies_only,
        status=status,
        error_category=error_category,
        start_date=start_dt,
        end_date=end_dt
    )

    # Transformasi manual untuk menjamin relasi domain_name & domain_url termap dengan baik
    result = []
    for inc in incidents:
        result.append(
            IncidentResponse(
                id=inc.id,
                domain_id=inc.domain_id,
                domain_name=inc.domain.name if inc.domain else "Domain Terhapus",
                domain_url=inc.domain.target_url if inc.domain else "",
                start_time=inc.start_time,
                end_time=inc.end_time,
                duration_seconds=inc.duration_seconds,
                qualifies_as_downtime=inc.qualifies_as_downtime,
                root_error_category=inc.root_error_category,
                root_error_message=inc.root_error_message,
                incident_status=inc.incident_status,
                created_at=inc.created_at
            )
        )
        
    return result

@router.get("/count")
def get_incidents_count(
    domain_id: Optional[int] = Query(None),
    qualifies_only: Optional[bool] = Query(None),
    status: Optional[str] = Query(None),
    error_category: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    repo = IncidentRepository(db)
    start_dt = None
    end_dt = None
    if start_date:
        start_dt = datetime.fromisoformat(start_date)
    if end_date:
        end_dt = datetime.fromisoformat(end_date)
        
    count = repo.count_all(
        domain_id=domain_id,
        qualifies_only=qualifies_only,
        status=status,
        error_category=error_category,
        start_date=start_dt,
        end_date=end_dt
    )
    return {"count": count}
