from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.repositories.base import BaseRepository
from app.models.incident import Incident
from app.models.domain import Domain
from typing import List, Optional, Dict, Any
from datetime import datetime, date, time

class IncidentRepository(BaseRepository):
    def get_by_id(self, incident_id: int) -> Optional[Incident]:
        return self.db.query(Incident).filter(Incident.id == incident_id).first()

    def get_active_by_domain(self, domain_id: int) -> Optional[Incident]:
        return self.db.query(Incident).filter(
            and_(
                Incident.domain_id == domain_id,
                Incident.incident_status == "ACTIVE"
            )
        ).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        domain_id: Optional[int] = None,
        qualifies_only: Optional[bool] = None,
        status: Optional[str] = None,
        error_category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Incident]:
        query = self.db.query(Incident).join(Domain)
        
        if domain_id is not None:
            query = query.filter(Incident.domain_id == domain_id)
        if qualifies_only is not None:
            query = query.filter(Incident.qualifies_as_downtime == qualifies_only)
        if status is not None:
            query = query.filter(Incident.incident_status == status)
        if error_category is not None:
            query = query.filter(Incident.root_error_category == error_category)
        if start_date is not None:
            query = query.filter(Incident.start_time >= start_date)
        if end_date is not None:
            query = query.filter(Incident.start_time <= end_date)
            
        return query.order_by(Incident.start_time.desc()).offset(skip).limit(limit).all()

    def count_all(
        self,
        domain_id: Optional[int] = None,
        qualifies_only: Optional[bool] = None,
        status: Optional[str] = None,
        error_category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        query = self.db.query(Incident)
        
        if domain_id is not None:
            query = query.filter(Incident.domain_id == domain_id)
        if qualifies_only is not None:
            query = query.filter(Incident.qualifies_as_downtime == qualifies_only)
        if status is not None:
            query = query.filter(Incident.incident_status == status)
        if error_category is not None:
            query = query.filter(Incident.root_error_category == error_category)
        if start_date is not None:
            query = query.filter(Incident.start_time >= start_date)
        if end_date is not None:
            query = query.filter(Incident.start_time <= end_date)
            
        return query.count()

    def create(self, domain_id: int, error_category: str, error_message: str) -> Incident:
        incident = Incident(
            domain_id=domain_id,
            start_time=datetime.utcnow(),
            qualifies_as_downtime=False,
            root_error_category=error_category,
            root_error_message=error_message,
            incident_status="ACTIVE"
        )
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def resolve(self, incident: Incident, end_time: datetime, qualifies_as_downtime: bool) -> Incident:
        incident.end_time = end_time
        incident.incident_status = "RESOLVED"
        incident.duration_seconds = int((end_time - incident.start_time).total_seconds())
        incident.qualifies_as_downtime = qualifies_as_downtime
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def update_qualify_status(self, incident: Incident, qualifies: bool) -> Incident:
        incident.qualifies_as_downtime = qualifies
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def get_downtime_today_seconds(self) -> int:
        today_start = datetime.combine(date.today(), time.min)
        # Hitung sum durasi dari incident yang qualifies_as_downtime=True dan dimulai hari ini
        result = self.db.query(func.sum(Incident.duration_seconds)).filter(
            and_(
                Incident.qualifies_as_downtime == True,
                Incident.start_time >= today_start
            )
        ).scalar()
        
        # Tambahkan durasi incident ACTIVE yang sedang berlangsung hari ini dan sudah qualifies_as_downtime
        active_incidents = self.db.query(Incident).filter(
            and_(
                Incident.incident_status == "ACTIVE",
                Incident.qualifies_as_downtime == True,
                Incident.start_time >= today_start
            )
        ).all()
        
        active_duration = sum(int((datetime.utcnow() - inc.start_time).total_seconds()) for inc in active_incidents)
        
        return (result or 0) + active_duration

    def get_summary_aggregates(self, start_dt: datetime, end_dt: datetime) -> Dict[str, Any]:
        # Total incident yang qualifies_as_downtime=True
        total_incidents = self.db.query(Incident).filter(
            and_(
                Incident.qualifies_as_downtime == True,
                Incident.start_time >= start_dt,
                Incident.start_time <= end_dt
            )
        ).count()

        # Total downtime seconds
        total_downtime = self.db.query(func.sum(Incident.duration_seconds)).filter(
            and_(
                Incident.qualifies_as_downtime == True,
                Incident.start_time >= start_dt,
                Incident.start_time <= end_dt
            )
        ).scalar() or 0

        # Top affected domains
        top_domains_query = self.db.query(
            Incident.domain_id,
            Domain.name,
            Domain.target_url,
            func.count(Incident.id).label("incident_count"),
            func.sum(Incident.duration_seconds).label("total_downtime_seconds")
        ).join(Domain).filter(
            and_(
                Incident.qualifies_as_downtime == True,
                Incident.start_time >= start_dt,
                Incident.start_time <= end_dt
            )
        ).group_by(
            Incident.domain_id, Domain.name, Domain.target_url
        ).order_by(
            func.sum(Incident.duration_seconds).desc()
        ).limit(5).all()

        # Error distribution
        error_dist_query = self.db.query(
            Incident.root_error_category,
            func.count(Incident.id)
        ).filter(
            and_(
                Incident.qualifies_as_downtime == True,
                Incident.start_time >= start_dt,
                Incident.start_time <= end_dt
            )
        ).group_by(
            Incident.root_error_category
        ).all()

        error_dist = {row[0] or "Unknown": row[1] for row in error_dist_query}

        top_domains = []
        for row in top_domains_query:
            top_domains.append({
                "domain_id": row[0],
                "domain_name": row[1],
                "target_url": row[2],
                "incident_count": row[3],
                "total_downtime_seconds": int(row[4] or 0)
            })

        return {
            "total_incidents": total_incidents,
            "total_downtime_seconds": int(total_downtime),
            "top_affected_domains": top_domains,
            "error_distribution": error_dist
        }
