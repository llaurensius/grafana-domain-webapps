from sqlalchemy.orm import Session
from app.models.incident import Incident
from app.schemas.incident import IncidentCreate, IncidentUpdate
from typing import Optional

class IncidentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_active_incident(self, domain_id: int) -> Optional[Incident]:
        """Ambil satu insiden terbuka (ACTIVE atau RECOVERY_PENDING) untuk domain tertentu."""
        return self.db.query(Incident).filter(
            Incident.domain_id == domain_id,
            Incident.status.in_(["ACTIVE", "RECOVERY_PENDING"])
        ).first()

    def get_all_open(self) -> list[Incident]:
        """
        Ambil SEMUA insiden terbuka (ACTIVE + RECOVERY_PENDING) dalam satu query bulk.
        Digunakan oleh IncidentService.process_metrics() untuk menghindari N+1 query.
        """
        return self.db.query(Incident).filter(
            Incident.status.in_(["ACTIVE", "RECOVERY_PENDING"])
        ).all()


    def get_by_domain(self, domain_id: int):
        return self.db.query(Incident).filter(Incident.domain_id == domain_id).all()

    def get_all(self, skip: int = 0, limit: int = 100):
        total = self.db.query(Incident).count()
        from app.models.domain import Domain
        results = self.db.query(Incident, Domain.url, Domain.name)\
            .join(Domain, Incident.domain_id == Domain.id)\
            .order_by(Incident.start_time.desc())\
            .offset(skip).limit(limit).all()
            
        formatted_data = []
        for inc, url, name in results:
            inc_dict = inc.__dict__.copy()
            inc_dict['domain_url'] = url
            inc_dict['domain_name'] = name
            formatted_data.append(inc_dict)
            
        return {"total": total, "data": formatted_data}

    def create(self, incident_in: IncidentCreate):
        db_obj = Incident(**incident_in.model_dump())
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: Incident, incident_in: IncidentUpdate):
        update_data = incident_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
