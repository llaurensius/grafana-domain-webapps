from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.domain import Domain
from app.schemas.domain import DomainCreate, DomainUpdate
from typing import List, Optional
import datetime

class DomainRepository(BaseRepository):
    def get_by_id(self, domain_id: int) -> Optional[Domain]:
        return self.db.query(Domain).filter(Domain.id == domain_id).first()

    def get_by_url(self, target_url: str) -> Optional[Domain]:
        return self.db.query(Domain).filter(Domain.target_url == target_url).first()

    def get_all(self, skip: int = 0, limit: int = 100, active_only: Optional[bool] = None) -> List[Domain]:
        query = self.db.query(Domain)
        if active_only is not None:
            query = query.filter(Domain.active == active_only)
        return query.order_by(Domain.id.desc()).offset(skip).limit(limit).all()

    def count_all(self, active_only: Optional[bool] = None) -> int:
        query = self.db.query(Domain)
        if active_only is not None:
            query = query.filter(Domain.active == active_only)
        return query.count()

    def create(self, domain_in: DomainCreate) -> Domain:
        domain = Domain(
            name=domain_in.name,
            target_url=domain_in.target_url,
            protocol=domain_in.protocol,
            probe_interval=domain_in.probe_interval,
            active=domain_in.active
        )
        self.db.add(domain)
        self.db.commit()
        self.db.refresh(domain)
        return domain

    def update(self, domain: Domain, domain_in: DomainUpdate) -> Domain:
        update_data = domain_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(domain, field, value)
        domain.updated_at = datetime.datetime.utcnow()
        self.db.commit()
        self.db.refresh(domain)
        return domain

    def delete(self, domain: Domain) -> None:
        self.db.delete(domain)
        self.db.commit()
