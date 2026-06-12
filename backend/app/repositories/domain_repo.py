from sqlalchemy.orm import Session
from app.models.domain import Domain
from app.schemas.domain import DomainCreate, DomainUpdate

class DomainRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        return self.db.query(Domain).all()

    def get_active(self):
        return self.db.query(Domain).filter(Domain.is_active == True).all()

    def get_by_id(self, domain_id: int):
        return self.db.query(Domain).filter(Domain.id == domain_id).first()

    def create(self, domain_in: DomainCreate):
        db_obj = Domain(**domain_in.model_dump())
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def bulk_create(self, domains_in: list[DomainCreate]):
        existing = {d.url: d for d in self.db.query(Domain).all()}
        db_objs_to_add = []
        seen_urls = set()
        
        for domain_in in domains_in:
            if domain_in.url in seen_urls:
                continue
            seen_urls.add(domain_in.url)
            
            if domain_in.url in existing:
                db_obj = existing[domain_in.url]
                db_obj.name = domain_in.name
                db_obj.is_active = domain_in.is_active
            else:
                db_objs_to_add.append(Domain(**domain_in.model_dump()))
                
        if db_objs_to_add:
            self.db.add_all(db_objs_to_add)
            
        self.db.commit()
        return []

    def update(self, db_obj: Domain, domain_in: DomainUpdate):
        update_data = domain_in.model_dump(exclude_unset=True)
        was_active = db_obj.is_active
        for field, value in update_data.items():
            setattr(db_obj, field, value)
            
        if was_active and not db_obj.is_active:
            from app.models.incident import Incident
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            active_incidents = self.db.query(Incident).filter(
                Incident.domain_id == db_obj.id, 
                Incident.status == "ACTIVE"
            ).all()
            for inc in active_incidents:
                duration = int((now - inc.start_time.replace(tzinfo=timezone.utc)).total_seconds())
                inc.status = "RESOLVED"
                inc.end_time = now
                inc.duration_seconds = duration
                inc.qualifies_as_downtime = inc.qualifies_as_downtime or (duration >= 295)
                
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, db_obj: Domain):
        from app.models.incident import Incident
        self.db.query(Incident).filter(Incident.domain_id == db_obj.id).delete()
        self.db.delete(db_obj)
        self.db.commit()

    def bulk_delete(self, domain_ids: list[int]):
        from app.models.incident import Incident
        self.db.query(Incident).filter(Incident.domain_id.in_(domain_ids)).delete(synchronize_session=False)
        self.db.query(Domain).filter(Domain.id.in_(domain_ids)).delete(synchronize_session=False)
        self.db.commit()
